$(function () {
  const csrftoken = Cookies.get("csrftoken");
  const searchCountry = async (inputCountry) => {
    const res = await fetch("/static/js/countries.json");
    const countries = await res.json();
    let fits = countries.filter((country) => {
      const regex = new RegExp(`^${inputCountry}`, "gi");
      if (country.name.match(regex) || country.code.match(regex))
        return country;
    });
    if (!fits) {
      return "";
    } else {
      return fits[0].code;
    }
  };
  // update address
  $(".updateForm").submit(async function (event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const plainData = Object.fromEntries(formData.entries());
    // replace country name with country code
    plainData.country = await searchCountry(plainData.country);
    console.log("updated country", plainData.country);
    const postData = Object.assign(plainData, {
      addr_id: $(this).attr("addrId"),
    });
    const res = await fetch("/account/address/", {
      method: "PUT",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(postData),
    });
    const data = await res.json();
    $(this).parents(".modal").modal("toggle");
    if (data.res == "1") {
      console.log(data);
      showMsg(data.msg, 1);
      setTimeout(function () {
        location.reload();
      }, 4000);
    } else {
      console.log(data);
      showMsg(data.errmsg, 0);
    }
  });
  // create new address
  $("#createForm").submit(async function (event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const plainData = Object.fromEntries(formData.entries());

    const res = await fetch("/account/address/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(plainData),
    });
    const data = await res.json();
    $(this).parents(".modal").modal("toggle");
    if (data.res == "1") {
      console.log(data);
      $("#newAddrButton").click();
      $(this)[0].reset();
      showMsg(data.msg, 1);
      setTimeout(function () {
        location.reload();
      }, 4000);
      //addToTable(plainData, data.new_id)
    } else {
      console.log(data);
      showMsg(data.errmsg, 0);
    }
  });

  // notice delegation here for dynamicly added address
  $("#addr-body").on("click", "a", async function (event) {
    event.preventDefault();
    let addrId = $(this).attr("addr-id");
    const res = await fetch("/account/address/", {
      method: "DELETE",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        addr_id: addrId,
      }),
    });
    const data = await res.json();
    if (data.res == "1") {
      console.log(data);
      $(this).parents("tr").remove();
      showMsg(data.msg, 1);
    } else {
      console.log(data);
      showMsg(data.errmsg, 0);
    }
  });
});
