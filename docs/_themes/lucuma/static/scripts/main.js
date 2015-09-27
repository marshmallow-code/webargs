function setupDropdowns(e){
    $(document).on('click', '[data-toggle="dropdown"]', function(e){
        e.preventDefault();
        e.stopPropagation();
        setupDropdown(this);
    });
}
setupDropdowns();

function setupDropdown(dd){
    var $dd = $(dd);
    var targetSel = $dd.attr('href');
    var $target = $(targetSel);
    if ($target.is(':visible')){
        $target.slideUp();
    } else {
        $target.slideDown();
    }
}

function setupPopup($section){
    $section.magnificPopup({
        delegate: 'a.image-reference',
        type: 'image',
        gallery: {
            enabled: true
        },
        zoom: {
            enabled: true,
            duration: 300,
            easing: 'ease-in-out'
        }
    });
}

function setupPopups(){
    // Each section is a separate gallery in this way
    $('.section a.image-reference').closest('.section').each(function(){
        var $section = $(this);
        setupPopup($section);
    });
}
setupPopups();
