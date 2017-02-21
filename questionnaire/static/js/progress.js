(function($){
    $(document).ready(function() {
        var request = {
            type: 'GET',
            url: progress_url + '?nocache=' + new Date().getTime(),
            dataType: 'json',
            success: function(data) {
                var progress = data.progress;

                var bar = $('#progress_bar').find('.ui-progress');
                bar.animate({'width': progress.toString() + '%'});
            }
        };

        $.ajax(request);
    });
})(jQuery);