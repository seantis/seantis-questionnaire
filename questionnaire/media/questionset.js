var qvalues = new Array(); // used as dictionary
var qtriggers = new Array();

function dep_check(expr) {
    var exprs = expr.split(",",2);
    var qnum = exprs[0];
    var value = exprs[1];
    var qvalue = qvalues[qnum];
    if(value.substring(0,1) == "!") {
      value = value.substring(1);
      return qvalue != value;
    }
    if(value.substring(0,1) == "<") {
      qvalue = parseInt(qvalue);
      if(value.substring(1,2) == "=") {
        value = parseInt(value.substring(2));
        return qvalue <= value;
      }
      value = parseInt(value.substring(1));
      return qvalue < value;
    }
    if(value.substring(0,1) == ">") {
      qvalue = parseInt(qvalue);
      if(value.substring(1,2) == "=") {
        value = parseInt(value.substring(2));
        return qvalue >= value;
      }
      value = parseInt(value.substring(1));
      return qvalue > value;
    }
    if(qvalues[qnum] == value) {
      return true;
    }
    return false;
}

function getChecksAttr(obj) {
    return obj.getAttribute('checks');
}

function statusChanged(obj, res) {
    if(obj.tagName == 'DIV') {
        obj.style.display = !res ? 'none' : 'block';
        return;
    }
    //obj.style.backgroundColor = !res ? "#eee" : "#fff";
    obj.disabled = !res;
}

function valchanged(qnum, value) {
    qvalues[qnum] = value;
    for (var t in qtriggers) {
        t = qtriggers[t];
        checks = getChecksAttr(t);
        var res = eval(checks);
        statusChanged(t, res)
    }
}

function addtrigger(elemid) {
    var elem = document.getElementById(elemid);
    if(!elem) {
      alert("addtrigger: Element with id "+elemid+" not found.");
      return;
    }
    qtriggers[qtriggers.length] = elem;
}
