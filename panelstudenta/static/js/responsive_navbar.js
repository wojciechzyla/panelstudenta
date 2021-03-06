$(document).ready(function() {
    let defaultHeaderHeight = 60;
     $(".header-own").css("height", defaultHeaderHeight);
     $("main").css("margin-top", defaultHeaderHeight);

    $(".navbar-button").on("click", function(){
        const smallMenu= $(".small-menu-default");
        smallMenu.toggleClass("small-menu");

        if (smallMenu.hasClass("small-menu")){
            const smallMenuHeight = parseInt($(".small-menu").css("height"));
            $(".header-own").css("height", defaultHeaderHeight + smallMenuHeight);
            $("main").css("margin-top", defaultHeaderHeight + smallMenuHeight);
        }else{
            $(".header-own").css("height", defaultHeaderHeight);
            $("main").css("margin-top", defaultHeaderHeight);
        }
    })

    $(window).resize(function(){
        const width = $( window ).width();
        if (width >= 768){
            $(".header-own").css("height", defaultHeaderHeight);
            $("main").css("margin-top", defaultHeaderHeight);
            const smallMenu= $(".small-menu-default");
            if (smallMenu.hasClass("small-menu")){
                smallMenu.removeClass("small-menu");
            }
        }
    })
});