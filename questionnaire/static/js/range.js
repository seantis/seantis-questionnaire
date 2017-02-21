(function($){$(document).ready(function() {
         
    // true if the native html5 range input type is supported by the browser
    var range_support = (function(){
        var el=document.createElement("input");
        el.setAttribute("type", "range");
        return el.type=="range";
    })();
                  
    // if range is not supported the input will be a simple text field
    // in which case the following function ensures that the values
    // in this text field are within the constraints of min, max, step
    var normalize_value = function(input) {
        var input = $(input);

        var min = parseFloat(input.attr('min'));
        var max = parseFloat(input.attr('max'));
        var step = parseFloat(input.attr('step'));
        var val = parseFloat(input.attr('value'));

        if (val > max) val = max;
        if (val < min) val = min; 

        // returns the number of digits after the decimal point
        var digits = function(value){
            var str = value.toString();
           
            if (str.indexOf('.') == -1 && str.indexOf(',') == -1)
                return 0;

            if (str.indexOf('.') > -1)
                return str.split('.')[1].length;
            else
                return str.split(',')[1].length;
        };

        // rounds the number to the next step
        var round = function(val, step) {
            return Math.round(val * (1 / step)) / (1 / step);
        };      
         
        // round the number and fix the digits
        return round(val, step).toFixed(digits(val));  
    };

    if (range_support) {
        $('.rangeinput input').change(function() {
            var label = $(this).parent().parent().find('label');
            var unit = label.attr('data-unit');
            label.html($(this).val() + unit);
        });
        $('.rangeinput input').trigger('change');
    } else {
        $('.rangeinput input').change(function() {
            $(this).val(normalize_value(this));
        }); 
    }

});})(jQuery);
