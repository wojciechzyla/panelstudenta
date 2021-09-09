$(document).ready(function(){
    $("#deleteModal").on("show.bs.modal", function(event){
        // Get the button that triggered the modal
        const button = $(event.relatedTarget);

        // Extract value from the custom data-* attribute
        const url = button.data("url");
        const filename = button.data("filename");
        const str_to_add = "Na pewno chcesz usunąć plik "+filename+" ?";
        console.log(str_to_add);

        //$("<h5>" + str_to_add + "</h5>").insertBefore($('#deleteModalLabel'));
        $(this).find('#deleteModalLabel').html(str_to_add);
        $(this).find('#confirm-delete').attr('action', url);
    });
});