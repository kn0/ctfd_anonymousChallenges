if ($('#challenges-board').length) {
    $('<div id=anonsubmit></div>').insertBefore('#challenges-board');
    $.get('plugins/ctfd_anonymousChallenges/assets/anonymous-challenge-submit_form.html', function (data) {
        $('#anonsubmit').html(data);

        var anon_submit_key = $('#anon-submit-key');
        var anon_answer_input = $('#anon-answer-input');
        anon_submit_key.unbind('click');
        anon_submit_key.click(function (e) {
            e.preventDefault();

            $.post(script_root + "/anonchal" , {
                key: anon_answer_input.val(),
                nonce: $('#nonce').val()
            }, function (data) {
                console.log(data);
                var result = $.parseJSON(JSON.stringify(data));

                var result_message = $('#anon-result-message');
                var result_notification = $('#anon-result-notification');
                result_notification.removeClass();
                result_message.text(result.message);

                if (result.status == -1) {
                    window.location = script_root + "/login?next=" + script_root + window.location.pathname + window.location.hash
                    return
                }
                else if (result.status == 0) { // Incorrect key
                    result_notification.addClass('alert alert-danger alert-dismissable text-center');
                    result_notification.slideDown();

                    anon_answer_input.removeClass("correct");
                    anon_answer_input.addClass("wrong");
                    setTimeout(function () {
                        anon_answer_input.removeClass("wrong");
                    }, 3000);
                }
                else if (result.status == 1) { // Challenge Solved
                    result_notification.addClass('alert alert-success alert-dismissable text-center');
                    result_notification.slideDown();

                    anon_answer_input.val("");
                    anon_answer_input.removeClass("wrong");
                    anon_answer_input.addClass("correct");
                }
                else if (result.status == 2) { // Challenge already solved
                    result_notification.addClass('alert alert-info alert-dismissable text-center');
                    result_notification.slideDown();

                    anon_answer_input.addClass("correct");
                }

                setTimeout(function () {
                    $('.alert').slideUp();
                    anon_submit_key.removeClass("disabled-button");
                    anon_submit_key.prop('disabled', false);
                }, 4500);
            });

            update();
        });

        anon_answer_input.keyup(function(event){
            if(event.keyCode == 13){
                anon_submit_key.click();
            }
        });
    });
}