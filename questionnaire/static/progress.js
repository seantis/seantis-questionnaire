(function($){
    $(document).ready(function() {
        var request = {
            type: 'GET',
            url: progress_url,
            dataType: 'json',
            success: function(data) {
                var progress = data.progress;
                console.log(progress);    

                var bar = $('#progress_bar').find('.ui-progress');
                bar.animate({'width': progress.toString() + '%'});
            },
            error: function(e) {
                console.log(e);
            }
        };

        $.ajax(request);
    });
})(jQuery);