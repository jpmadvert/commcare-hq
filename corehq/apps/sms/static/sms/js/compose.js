hqDefine('sms/js/compose', function() {
    var initialPageData = hqImport('hqwebapp/js/initial_page_data');

    $(function(){
        $("#hint_id_recipients").addClass("alert alert-info");
        $("#hint_id_message").addClass("alert alert-info");
        $("#id_message").on('keyup', function () {
            var max_char = 160,
                current_count = $(this).val().length,
                cc_message = "",
                chars_remaining = max_char - current_count,
                $char_count = $("#hint_id_message");

            if (chars_remaining < 0) {
                $char_count.addClass("alert-danger").removeClass('alert-info');
            } else {
                $char_count.removeClass("alert-danger").addClass('alert-info');
            }

            cc_message = current_count + " character";
            if (current_count !== 1) {
                cc_message = cc_message + "s";
            }

            cc_message = cc_message + " (" + max_char + " max)";
            $char_count.text(cc_message);
        });


        $('.sms-typeahead').multiTypeahead({
            source: initialPageData.get('sms_contacts')
        }).focus();
    });
});
