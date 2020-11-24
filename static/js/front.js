$(function () {
  /* ===============================================================
         LIGHTBOX
      =============================================================== */
  lightbox.option({
    resizeDuration: 200,
    wrapAround: true,
  });

  /* ===============================================================
         PRODUCT SLIDER
      =============================================================== */
  $(".product-slider").owlCarousel({
    items: 1,
    thumbs: true,
    thumbImage: false,
    thumbsPrerendered: true,
    thumbContainerClass: "owl-thumbs",
    thumbItemClass: "owl-thumb-item",
  });

  /* ===============================================================
         PRODUCT QUNATITY
      =============================================================== */
  $(".dec-btn").click(function (event) {
    event.stopPropagation();
    let count = $(this).siblings("input").val();
    // check if dec in shopping cart page
    let cartChecker = $(this).siblings("input").hasClass("qty-cart");
    let skuId = $(this).siblings("input").attr("sku-id");
    if (cartChecker) {
      updateRemoteCart(skuId, count - 1);
      console.log("dec", updateErr);
    }
    // updateErr == True, remote database update failed, do not change item qty
    if (updateErr === true) {
      return;
    }
    // else continue to reset qty
    count = parseInt(count) - 1;
    if (count <= 0) {
      count = 1;
    }
    $(this).siblings("input").val(count);
    console.log("dec", count);
    if (cartChecker) {
      updateCartPage();
    }
  });

  $(".inc-btn").click(function (event) {
    event.stopPropagation();
    // get stock as maximum input qty
    let stock = parseInt($(this).siblings("input").attr("stock"));
    let count = parseInt($(this).siblings("input").val());
    if (count + 1 > stock) {
      return;
    }
    let cartChecker = $(this).siblings("input").hasClass("qty-cart");
    let skuId = $(this).siblings("input").attr("sku-id");
    if (cartChecker) {
      console.log("inc", updateErr);
      updateRemoteCart(skuId, count + 1);
    }
    if (updateErr === true) {
      return;
    }
    // qty should not be greater than stock
    if (count < stock) {
      count = count + 1;
    } else {
      count = stock;
    }
    $(this).siblings("input").val(count);
    console.log("inc", count);
    if (cartChecker) {
      updateCartPage();
    }
  });
  /* ===============================================================
           BOOTSTRAP SELECT
        =============================================================== */
  $(".selectpicker").on("change", function () {
    $(this)
      .closest(".dropdown")
      .find(".filter-option-inner-inner")
      .addClass("selected");
  });

  /* ===============================================================
           TOGGLE ALTERNATIVE BILLING ADDRESS
        =============================================================== */
  $("#alternateAddressCheckbox").on("change", function () {
    var checkboxId = "#" + $(this).attr("id").replace("Checkbox", "");
    $(checkboxId).toggleClass("d-none");
  });

  /* ===============================================================
           AJAX REQUESTS ON SHOPPING CART
        =============================================================== */
  // $('a[href="#"]').on("click", function (e) {
  //   e.preventDefault();
  // });
  const csrftoken = Cookies.get("csrftoken");
  $.ajaxSetup({
    beforeSend: function (xhr) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    },
  });

  $(".add-cart").click(function (event) {
    event.preventDefault();
    let skuId = $(this).attr("sku-id");
    let qty = "qty-" + skuId;
    let count = $(`#${qty}`).val() || 1;
    $.ajax({
      url: "/cart/add/",
      method: "post",
      data: {
        sku_id: skuId,
        count: count,
      },
      dataType: "json",
      success: function (data) {
        if (data.res == "1") {
          $("#cart-count").text(data.cart_count);
        } else {
          alert(data.errmsg);
          location.reload();
        }
      },
      fail: function () {
        alert("Request failed");
      },
    });
  });

  let updateErr = false;
  function updateRemoteCart(skuId, count) {
    $.ajax({
      url: "/cart/update/",
      method: "post",
      data: {
        sku_id: skuId,
        count: count,
      },
      dataType: "json",
      success: function (data) {
        if (data.res == "1") {
          updateErr = false;
          // totalCount = data.total_count;
          // subtotal = data.subtotal;
        } else {
          updateErr = true;
          alert(data.errmsg);
          location.reload();
        }
      },
      fail: function () {
        alert("Request failed");
      },
    });
  }

  function updateCartPage() {
    let totalCount = 0;
    let subtotal = 0;
    let cartCount = 0;
    $(".qty-cart").each(function () {
      let skuId = $(this).attr("sku-id");
      let price = $(`#price-${skuId}`).text();
      let total = parseInt($(this).val()) * parseInt(price);

      $(`#product-total-${skuId}`).text(total);
      subtotal += total;
      totalCount += parseInt($(this).val());
      cartCount += 1;
    });
    $(".total-count").text(totalCount);
    $(".subtotal").text(subtotal);
    $(".total-price").text(subtotal);
    $("#cart-count").text(cartCount);
  }
  // async function updateRemote(skuId, count) {
  //   data = { sku_id: skuId, count: count };
  //   let response = await fetch("/cart/update/", {
  //     method: "POST",
  //     headers: { "X-CSRFToken": csrftoken },
  //     body: JSON.stringify(data),
  //   });
  //   console.log(response);
  //   if (response.res == "0") {
  //     updateErr = true;
  //     throw new Error(`Request error: ${response.errmsg}`);
  //   } else {
  //     updateErr = false;
  //     return await response.json();
  //   }
  // }
  $(".cart-del").click(function (event) {
    event.preventDefault();
    let skuParentEl = $(this).parents("tr");
    let skuId = $(this).attr("sku-id");
    let count = $(`#qty-${skuId}`).val();
    $.ajax({
      url: "/cart/delete/",
      method: "post",
      data: {
        sku_id: skuId,
        count: count, // no need but for integrity
      },
      dataType: "json",
      success: function (data) {
        if (data.res == "1") {
          skuParentEl.remove();
          updateCartPage();
          $(".total-count").text(data.total_count);
        } else {
          alert(data.errmsg);
          location.reload();
        }
      },
      fail: function () {
        alert("Request failed");
      },
    });
  });
});

/* ===============================================================
     COUNTRY SELECT BOX FILLING
  =============================================================== */
$.getJSON("/static/js/countries.json", function (data) {
  $.each(data, function (key, value) {
    var selectOption =
      "<option value='" +
      value.name +
      "' data-dial-code='" +
      value.dial_code +
      "'>" +
      value.name +
      "</option>";
    $("select.country").append(selectOption);
  });
});
