import time
import logging
from flask import request, jsonify, session
from CTFd.plugins.challenges import BaseChallenge, CHALLENGE_CLASSES, get_chal_class
from CTFd.plugins import register_plugin_assets_directory, register_plugin_script
from CTFd.models import db, Solves, WrongKeys, Keys, Challenges, Files, Tags, Hints, Teams
from CTFd import utils
from .model import AnonymousChallenge
from CTFd.utils.decorators import (
    during_ctf_time_only,
    viewable_without_authentication
)
from .model import AnonymousChallenge


class CTFdAnonymousChallenge(BaseChallenge):
    id = "anonymous"  # Unique identifier used to register challenges
    name = "anonymous"  # Name of a challenge type
    templates = {  # Nunjucks templates used for each aspect of challenge editing & viewing
        'create': '/plugins/ctfd_anonymousChallenges/assets/anonymous-challenge-create.njk',
        'update': '/plugins/ctfd_anonymousChallenges/assets/anonymous-challenge-update.njk',
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        'create': '/plugins/ctfd_anonymousChallenges/assets/anonymous-challenge-create.js',
        'update': '/plugins/ctfd_anonymousChallenges/assets/anonymous-challenge-update.js',
    }

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        # Create challenge
        chal = AnonymousChallenge(
            name=request.form['name'],
            value=request.form['value'],
            category=request.form['category'],
            type=request.form['chaltype'],
        )

        chal.hidden = True  # The challenge should always be hidden
        chal.max_attempts = 0  # Unlimited attempts for this type of challenge

        db.session.add(chal)
        db.session.commit()

        flag = Keys(chal.id, request.form['key'], 'static')  # request.form['key_type[0]'])
        if request.form.get('keydata'):
            flag.data = request.form.get('keydata')

        db.session.add(flag)
        db.session.commit()

        files = request.files.getlist('files[]')
        for f in files:
            utils.upload_file(file=f, chalid=chal.id)

        db.session.commit()

    @staticmethod
    def read(challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """

        data = {
            'id': challenge.id,
            'name': challenge.name,
            'value': challenge.value,
            'description': challenge.description,
            'category': challenge.category,
            'hidden': True,
            'max_attempts': 0,
            'type': challenge.type,
            'type_data': {
                'id': CTFdAnonymousChallenge.id,
                'name': CTFdAnonymousChallenge.name,
                'templates': CTFdAnonymousChallenge.templates,
                'scripts': CTFdAnonymousChallenge.scripts,
            },
        }

        return challenge, data

    @staticmethod
    def update(challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        challenge.name = request.form['name']
        # challenge.description = request.form['description']
        challenge.value = int(request.form.get('value', 0)) if request.form.get('value', 0) else 0
        challenge.category = request.form['category']
        db.session.commit()
        db.session.close()

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.

        :param challenge:
        :return:
        """
        WrongKeys.query.filter_by(chalid=challenge.id).delete()
        Solves.query.filter_by(chalid=challenge.id).delete()
        Keys.query.filter_by(chal=challenge.id).delete()
        files = Files.query.filter_by(chal=challenge.id).all()
        for f in files:
            utils.delete_file(f.id)
        Files.query.filter_by(chal=challenge.id).delete()
        Tags.query.filter_by(chal=challenge.id).delete()
        Hints.query.filter_by(chal=challenge.id).delete()
        AnonymousChallenge.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()


    @staticmethod
    def solve(team, chal, request):
        """
        This method is used to insert Solves into the database in order to mark a challenge as solved.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        # Disabled for cyphercon
        # provided_key = request.form['key'].strip()
        # solve = Solves(teamid=team.id, chalid=chal.id, ip=utils.get_ip(req=request), flag=provided_key)
        # db.session.add(solve)
        # db.session.commit()
        # db.session.close()

    @staticmethod
    def attempt(chal, request):
        """This method is not used"""

    @staticmethod
    def fail(team, chal, request):
        """This method is not used"""


def load(app):
    # Create new anonymous_challenge table if necessary
    app.db.create_all()

    # Register new challenge type
    CHALLENGE_CLASSES["anonymous"] = CTFdAnonymousChallenge

    # Register plugin assets
    register_plugin_assets_directory(app, base_path='/plugins/ctfd_anonymousChallenges/assets/')
    register_plugin_script('/plugins/ctfd_anonymousChallenges/assets/anonymous-challenge-submit.js')

    # Register custom route to check submissions

    @app.route('/anonchal', methods=['POST'])
    @during_ctf_time_only
    @viewable_without_authentication()
    def anonchal():
        if utils.ctf_paused():
            return jsonify({
                'status': 3,
                'message': '{} is paused'.format(utils.ctf_name())
            })

        if utils.is_admin() or (
                utils.authed() and
                utils.is_verified() and
                (utils.ctf_started() or utils.view_after_ctf())):

            team = Teams.query.filter_by(id=session['id']).first()
            provided_key = request.form['key'].strip()
            logger = logging.getLogger('keys')
            data = (
                time.strftime("%m/%d/%Y %X"),
                session['username'].encode('utf-8'),
                provided_key.encode('utf-8'),
                utils.get_kpm(session['id'])
            )

            # Anti-bruteforce / KPM is based on last failed key (not logged), so sleep instead.
            time.sleep(2)

            # Find challenge by looking up the provided flag
            key = db.session.query(Keys).\
                join(AnonymousChallenge).\
                filter(Keys.flag == provided_key).first()

            if not key:
                logger.info("[{0}] {1} submitted {2} with kpm {3} [WRONG]".format(*data))
                return jsonify({'status': 0, 'message': 'Invalid Flag'})

            chal = AnonymousChallenge.query.filter_by(id=key.chal).first()

            chal_class = get_chal_class(chal.type)
            solves = Solves.query.filter_by(teamid=session['id'], chalid=chal.id).first()

            # If team hasn't solved challenge yet, save the solve
            if not solves:
                # We already know the flag is correct because we checked it already
                chal_class.solve(team=team, chal=chal, request=request)
                logger.info("[{0}] {1} submitted {2} with kpm {3} [CORRECT]".format(*data))
                return jsonify({'status': 1, 'message': "Correct"})

            # Otherwise, raise an error
            else:
                logger.info("{0} submitted {1} with kpm {2} [ALREADY SOLVED]".format(*data))
                return jsonify({'status': 2, 'message': 'You already solved this'})
        else:
            return jsonify({
                'status': -1,
                'message': "You must be logged in to solve a challenge"
            })
