function loadGroups(accountingUrl, userId){
    let getGroupsUrl = accountingUrl+"/groups/"+userId;

    $.get({
        url: getGroupsUrl,
        dataType: "json",
        success: (data) => {
            $("#userGroups").html("");
            for (el of data){
                $("#userGroups").append(`<div class="d-flex flex-row align-items-center justify-content-between file-row p-1 mb-2">
                    <a href="http://localhost:5000/accounting/${el.groupId}" class="default-link file-link">
                        <div class="file-name">
                            <p class="m-0">${el.groupName}</p>
                        </div>
                    </a>
                    <button type="button" class="btn btn-danger btn-sm ml-1 delete-button" data-toggle="modal" data-target="#deleteModal" data-groupid=${el.groupId} data-groupname=${el.groupName}>Usuń</button>
                </div>`);
            }

            $("#userGroups").append(`<div class="modal fade" id="deleteModal" tabindex="-1" role="dialog" aria-labelledby="deleteModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
              <div class="modal-content modal-content-own">
                <div class="modal-header">
                  <h5 class="modal-title" id="deleteModalLabel"></h5>
                  <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true" class="modal-close-own">&times;</span>
                  </button>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" data-dismiss="modal">Nie</button>
                  <button type="button" class="btn btn-danger" id="deleteGroupButton" data-dismiss="modal">Usuń</button>
                </div>
              </div>
            </div>
          </div>`);
        },
        error: (resp) => {
            if (resp.status >= 500 || resp.status < 200){
              $("#userGroups").html("<div><p>Problem z załadowaniem grup</p></div>");
            }else{
                $("#userGroups").html("<div><p>Nie masz żadnych grup</p></div>");
            }
        }
    });
}


$(document).ready(function (){
    const accountingUrl = $("#flaskData").data("accountingUrl");
    const userId = $("#flaskData").data("userId");
    let addGroupUrl = accountingUrl+"/group";

    loadGroups(accountingUrl, userId);

    $("#addGroupButton").on("click", function(){
        let dataJson = JSON.stringify({
            groupName: $("input#group-name").val(),
            userId: userId
        });
        $.post({
            url: addGroupUrl,
            dataType: "json",
            contentType: "application/json",
            data: dataJson,
            success: () => {
                console.log("dodano grupe");
                loadGroups(accountingUrl, userId);
            },
            error: () => {
                console.log("problem z dodaniem grupy");
            }
        });
    });

    $("body").on("click", function(e){
        if ($(e.target).hasClass('delete-button')){
            let groupName = $(e.target).data("groupname");
            let groupId = $(e.target).data("groupid");
            let str_to_add = "Na pewno chcesz usunąć grupę "+groupName+" ?";
            $('#deleteModalLabel').html(str_to_add);
            $("#deleteGroupButton").attr("groupid", groupId);

            $("#deleteGroupButton").on("click", function(e){
                console.log("usuwam");
                let groupId = $(this).attr("groupid");
                let deleteUrl = accountingUrl+"/group/"+groupId;
                $.ajax({
                    url: deleteUrl,
                    type: 'DELETE',
                    success: () => {
                        console.log("group was deleted");
                        loadGroups(accountingUrl, userId)
                    },
                    error: () => {
                        console.log("group was not deleted");
                    }
                });
            });
        }
    });
});