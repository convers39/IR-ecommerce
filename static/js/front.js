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
    var count = $(this).siblings("input").val();
    count = parseInt(count) - 1;
    if (count <= 0) {
      count = 1;
    }
    $(this).siblings("input").val(count);
  });

  $(".inc-btn").click(function (event) {
    event.stopPropagation();
    var stock = $(this).siblings("input").attr("stock");
    var count = $(this).siblings("input").val();
    if (parseInt(count) < parseInt(stock)) {
      count = parseInt(count) + 1;
    } else {
      count = parseInt(stock);
    }
    $(this).siblings("input").val(count);
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
           DISABLE UNWORKED ANCHORS
        =============================================================== */
  $('a[href="#"]').on("click", function (e) {
    e.preventDefault();
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
