function loadParticipants(accountingUrl, groupId){
    let getUsersUrl = accountingUrl+`/group/${groupId}/participants`;
    $.get({
        url: getUsersUrl,
        dataType: "json",
        success: (data) => {
            let $participants = $("#participants");
            $participants.html("");
            if ($('#participants-background').length){
                $("#participants-background").remove();
            }
            for(el of data){
                $participants.append(`<div class="d-flex flex-row align-items-center justify-content-between file-row p-1 mb-2">
                <div class="file-link">
                    <div class="file-name">
                        <p class="m-0" data-participant-id="${el.participantId}">${el.name}</p>
                    </div>
                </div>
            </div>`);
            }
            $("body").append(`<div id="participants-background"></div>`);
        }
    });
}

function loadExpenditures(accountingUrl, participantId){
    let getUserUrl = accountingUrl+`/participant/${participantId}`;
    $.get({
        url: getUserUrl,
        dataType: "json",
        success: (data) => {
            $("#expenditures-content").html("");
            if ($("#expenditures").is(':visible')){
                for (el of data.expenditureDto){
                    $("#expenditures-content").append(`<div>${el.title} | koszt: ${el.cost}</div>`)
                }
            }
        }
    });
}

$(document).ready(function (){
    const accountingUrl = $("#flaskData").data("accountingUrl");
    const userId = $("#flaskData").data("userId");
    const groupId = $("#flaskData").data("groupId");
    $.get({
        url:accountingUrl+"/group/"+groupId,
        dataType: "json",
        success: (data) => {
            $("#app-title").html(`Użytkownicy grupy ${data.groupName}`);
        },
        error: () => {
            $("#app-title").html(`Problem z znalezieniem nazwy grupy`);
        }
    });

    loadParticipants(accountingUrl, groupId);

    $("#addParticipantButton").on("click", function(){
        let addUserUrl = accountingUrl+`/participant`
        let dataJson = JSON.stringify({
            name: $("input#participant-name").val(),
            groupId: groupId
        });
        $.post({
            url: addUserUrl,
            dataType: "json",
            contentType: "application/json",
            data: dataJson,
            success: () => {
                console.log("dodano usera");
                loadParticipants(accountingUrl, groupId);
            },
            error: () => {
                console.log("problem z dodaniem usera");
            }
        });
    });
    
    $("body").on("click", function(e){
        if ($(e.target).hasClass('m-0')){
            if ($("#participants-background").is(':hidden')){
                $("#expenditures").toggle();
                $("#participants-background").toggle();
                $("#expenditures").data("participantName", $(e.target).text());
                $("#expenditures").data("participantId", $(e.target).data("participantId"));
                $("#expenditures-title").html(`<p class="m-0">Wydatki użytkownika <b>${$(e.target).text()}</b>`);
                if ($(window).width() < 2000){
                    $("#expenditures").css("width", "70%");
                }else{
                    $("#expenditures").css("width", 1500);
                }
                let $setHeight = $("#expenditures").height()-$("#expenditures-title").height()-$("#expenditures-add").height()-60;
                $("#expenditures-content").height($setHeight);
                loadExpenditures(accountingUrl, $(e.target).data("participantId"));
            }

        }else if(e.target.id == "closeExpenditures"){
            if ($("#participants-background").is(':visible')){
                $("#participants-background").toggle();
                $("#expenditures").toggle();
            }

        }else if(e.target.id == "addExpenditureButton"){
            let dataJson = JSON.stringify({
                cost: $("input#expenditure-cost").val(),
                title: $("input#expenditure-name").val(),
                participantId: $("#expenditures").data("participantId")
            });
            $.post({
                url: accountingUrl+"/expenditure",
                dataType: "json",
                contentType: "application/json",
                data: dataJson,
                success: () => {
                    console.log("dodano wydatek");
                    loadExpenditures(accountingUrl, $("#expenditures").data("participantId"));
                },
                error: () => {
                    console.log("problem z dodaniem wydatku");
                }
            });
        }
    });

    $(window).on("resize", function(e){
        if($("#expenditures").is(':visible')){
            let $setHeight = $("#expenditures").height()-$("#expenditures-title").height()-$("#expenditures-add").height()-60;
                $("#expenditures-content").height($setHeight);
        }
    });
});