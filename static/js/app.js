$(function () {
  $("#ajaxSaveBtn").on("click", function () {
    const ticketId = $(this).data("ticket-id");
    const status = $("#ajaxStatus").val();
    const priority = $("#ajaxPriority").val();

    $("#ajaxMsg").text("Saving...");

    $.ajax({
      url: `/tickets/${ticketId}/ajax_update`,
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ status, priority }),
      success: function (res) {
        if (res.ok) {
          $("#ajaxMsg").text("Updated successfully!");
          $("#statusBadge").text(status);
          $("#priorityText").text(priority);
        } else {
          $("#ajaxMsg").text(res.message || "Error.");
        }
      },
      error: function (xhr) {
        const msg = (xhr.responseJSON && xhr.responseJSON.message) ? xhr.responseJSON.message : "Error.";
        $("#ajaxMsg").text(msg);
      }
    });
  });
});
