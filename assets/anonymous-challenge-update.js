$('#submit-key').click(function (e) {
    submitkey($('#chalid').val(), $('#answer').val())
});

$('#submit-keys').click(function (e) {
    e.preventDefault();
    $('#update-keys').modal('hide');
});

function loadchal(id, update) {
    $.get(script_root + '/admin/chal/' + id, function(obj){
        $('#desc-write-link').click(); // Switch to Write tab
        if (typeof update === 'undefined')
            $('#update-challenge').modal();
    });
}


function openchal(id){
    loadchal(id);
}

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});
