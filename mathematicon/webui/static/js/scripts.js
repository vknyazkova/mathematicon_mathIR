function switchLang(lang){
    $("[data-" + lang + "]").text(function(i, e) {
        return $(this).data(lang);
    });
};

