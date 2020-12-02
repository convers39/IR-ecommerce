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
  $(".dec-btn").click(async function (event) {
    event.stopPropagation();
    try {
      let count = $(this).siblings("input").val();
      // check if dec in shopping cart page
      let cartChecker = $(this).siblings("input").hasClass("qty-cart");
      let skuId = $(this).siblings("input").attr("sku-id");
      // console.log("inc", skuId, count);
      if (parseInt(count) - 1 <= 0) {
        showMsg("Cannot be less than 1 item", 0);
        return;
      }
      if (cartChecker) {
        let data = await updateRemote(skuId, count - 1);
        if (data.res == "1") {
          updateErr = false;
          count = parseInt(count) - 1;
          $(this).siblings("input").val(count);
          updateCartPage();
        } else {
          // updateErr == True, remote database update failed, do not change item qty
          updateErr = true;
          showMsg(data.errmsg, 0);
        }
      } else {
        // if not in cart page
        count = parseInt(count) - 1;
        $(this).siblings("input").val(count);
      }
    } catch (e) {
      showMsg("Invalid item count", 0);
    }
  });

  $(".inc-btn").click(async function (event) {
    event.stopPropagation();
    // try to parse qty and stock as maximum input qty
    try {
      let stock = parseInt($(this).siblings("input").attr("stock"));
      let count = parseInt($(this).siblings("input").val());

      // do not increase if count equals to stock
      if (count + 1 > stock) {
        showMsg("Out of inventory", 0);
        return;
      }
      // check if increase in the cart page
      let cartChecker = $(this).siblings("input").hasClass("qty-cart");
      let skuId = $(this).siblings("input").attr("sku-id");
      if (cartChecker) {
        let data = await updateRemote(skuId, count + 1);
        if (data.res == "1") {
          updateErr = false;
          count = count + 1;
          $(this).siblings("input").val(count);
          // update cart page if increase successfully
          updateCartPage();
        } else {
          updateErr = true;
          // alert(data.errmsg);
          showMsg(data.errmsg, 0);
        }
      } else {
        // if not in cart page
        count = count + 1;
        $(this).siblings("input").val(count);
      }
    } catch (e) {
      showMsg("Invalid item count", 0);
    }
  });

  let updateErr = false;
  const updateRemote = async (skuId, count) => {
    const res = await fetch("/cart/update/", {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken, "Content-Type": "application/json" },
      body: JSON.stringify({ sku_id: skuId, count: count }),
    });
    return (data = await res.json());
  };

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
  // $.ajaxSetup({
  //   beforeSend: function (xhr) {
  //     xhr.setRequestHeader("X-CSRFToken", csrftoken);
  //   },
  // });

  // retrieve csrftoken
  const csrftoken = Cookies.get("csrftoken");

  // change cart item qty by input number manually
  let preCount = 0;
  $(".qty-cart").focus(function () {
    preCount = $(this).val();
  });
  $(".qty-cart").blur(async function () {
    let count = $(this).val();
    let skuId = $(this).attr("sku-id");
    let stock = $(this).attr("stock");
    if (
      isNaN(count) ||
      count.trim().length == 0 ||
      parseInt(count) <= 0 ||
      parseInt(count) > stock
    ) {
      $(this).val(preCount);
      showMsg("Invalid item count", 0);
      return;
    }
    let data = await updateRemote(skuId, count);
    if (data.res == "1") {
      $(this).val(count);
      updateCartPage();
    } else {
      showMsg(data.errmsg, 0);
      // location.reload();
    }
  });

  // add or remove to wishlist
  $(".wishlist").click(async function (event) {
    event.preventDefault();
    let skuId = $(this).attr("sku-id");
    const res = await fetch("/account/wishlist/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sku_id: skuId }),
    });
    let data = await res.json();
    console.log(data);
    if (data.res == "1") {
      showMsg(data.msg, 1);
      $("#wishlist-count").text(data.wish_count);
      if ($(this).hasClass("account")) {
        $(this).parents("tr").remove();
      }
    } else {
      showMsg(data.errmsg, 0);
      // location.reload();
    }
  });

  // add cart item
  $(".add-cart").click(async function (event) {
    event.preventDefault();
    let skuId = $(this).attr("sku-id");
    let qty = "qty-" + skuId;
    let count = $(`#${qty}`).val() || 1;
    //console.log("add cart", skuId, count);
    const res = await fetch("/cart/add/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sku_id: skuId, count: count }),
    });
    let data = await res.json();
    if (data.res == "1") {
      $("#cart-count").text(data.cart_count);
      $(this).find("i").toggleClass("fa-heart fa-heart-o");
      showMsg(data.msg, 1);
    } else {
      showMsg(data.errmsg, 0);
      // location.reload();
    }
  });

  // delete cart item
  $(".cart-del").click(async function (event) {
    event.preventDefault();
    let skuParentEl = $(this).parents("tr");
    let skuId = $(this).attr("sku-id");
    let count = $(`#qty-${skuId}`).val();
    console.log("add delete", skuId, count);
    const res = await fetch("/cart/delete/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sku_id: skuId, count: count }),
    });
    let data = await res.json();
    if (data.res == "1") {
      skuParentEl.remove();
      updateCartPage();
      // $(".total-count").text(data.total_count);
    } else {
      alert(data.errmsg);
      // location.reload();
    }
  });

  // update shopping cart page when editing
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
// append message to message area, fade after timeout
function showMsg(msg, resCode) {
  let label = resCode == 0 ? "warning" : "success";
  let msgEl = `
    <div class="alert alert-${label} alert-dismissable" role="alert">
      <button type="button" class="close" data-dismiss="alert" aria-hidden="true" >
        &times;
      </button>
      ${msg}
    </div>
    `;
  $(".message-area").append(msgEl).hide().slideDown(500, 0).fadeIn(1000, 0);
  setTimeout(() => {
    $(".alert")
      .fadeTo(500, 0)
      .slideUp(500, function () {
        $(this).remove();
      });
  }, 3000);
}
