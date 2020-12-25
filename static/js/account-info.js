$(function () {
  const csrftoken = Cookies.get("csrftoken");
  let inputAreas = $("#userInfo").find("input");
  inputAreas.each(function () {
    $(this).prop("readonly", true);
  });

  $("#change").click(function (event) {
    event.preventDefault();
    //$('#changeButton').prop('hidden', true);
    $("#changeButton").toggle();
    $("#saveButton").toggle();
    inputAreas.each(function () {
      $(this).removeAttr("readonly");
    });
  });

  $("#cancel").click(function (event) {
    event.preventDefault();
    $("#changeButton").toggle();
    $("#saveButton").toggle();
    inputAreas.each(function () {
      $(this).prop("readonly", true);
    });
  });

  $("#userInfo").submit(async function (event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const plainData = Object.fromEntries(formData.entries());
    const res = await fetch("/account/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(plainData),
    });
    const data = await res.json();
    if (data.res == "1") {
      console.log(data);
      $("#changeButton").toggle();
      $("#saveButton").toggle();
      inputAreas.each(function () {
        let trimed = $.trim($(this).val());
        $(this).val(trimed);
        $(this).prop("readonly", true);
      });
      showMsg(data.msg, 1);
    } else {
      console.log(data);
      showMsg(data.errmsg, 0);
    }
  });

  $("#passwordForm").submit(async function (event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const plainData = Object.fromEntries(formData.entries());
    //let current = $('#currentPassword').val();
    //let newPassword = $('#newPassword').val();
    //let confirmNewPassword = $('#confirmNewPassword').val();

    const res = await fetch("/account/passwordreset/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(plainData),
    });
    const data = await res.json();
    if (data.res == "1") {
      console.log(data);
      $("#resetPassword").click();
      $("#passwordForm")[0].reset();
      showMsg(data.msg, 1);
    } else {
      console.log(data);
      showMsg(data.errmsg, 0);
    }
  });
});
