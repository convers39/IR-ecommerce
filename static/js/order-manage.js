$(function () {
  let remaining = $("#countdown").text();

  function countdownTimer() {
    //const difference = +new Date("2020-01-01") - +new Date();
    const difference = 1000 * 60 * 60 * 24 - 10;
    let remaining = "Expired";

    if (difference > 0) {
      const parts = {
        //days: Math.floor(difference / (1000 * 60 * 60 * 24)),
        hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
        minutes: Math.floor((difference / 1000 / 60) % 60),
        //seconds: Math.floor((difference / 1000) % 60),
      };
      remaining = Object.keys(parts)
        .map((part) => {
          return `${parts[part]} ${part}`;
        })
        .join(" ");
    }

    document.getElementById("countdown").innerHTML = remaining;
  }

  //countDownTimer();
  //setInterval(countdownTimer, 1000);

  const csrftoken = Cookies.get("csrftoken");
  // redirect to checkout
  var stripe = Stripe("{{ stripe_key }}");
  $(".payment").click(async function (event) {
    event.preventDefault();
    let sessionId = $(this).attr("session");
    // retrieve new session id if payment session expired,
    // which will set session id to empty string
    if (!sessionId) {
      let orderId = $(this).attr("orderId");
      const res = await fetch("/order/paymentrenew/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          order_id: orderId,
        }),
      });
      const data = await res.json();
      if (data.res == "1") {
        const sessionId = data.session.id;
      } else {
        showMsg(data.errmsg, 0);
        return;
      }
    }
    console.log(sessionId);
    const paymentSession = await stripe.redirectToCheckout({
      sessionId: sessionId,
    });
    if (paymentSession.error) {
      showErrMsg(paymentSession.error.message);
    }
  });

  // request a cancellation
  $(".cancel").click(async function (event) {
    event.preventDefault();
    let orderId = $(this).attr("orderId");
    const res = await fetch("/order/cancel/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        order_id: orderId,
      }),
    });
    const data = await res.json();
    console.log(data);
    if (data.res == "1") {
      showMsg(data.msg, 1);
      setTimeout(function () {
        location.reload();
      }, 3000);
    } else {
      showMsg(data.errmsg, 0);
      return;
    }
  });

  // delete an order
  $(".order-del").click(async function (event) {
    event.preventDefault();
    let orderId = $(this).attr("orderId");
    const res = await fetch("/order/cancel/", {
      method: "DELETE",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        order_id: orderId,
      }),
    });
    const data = await res.json();
    console.log(data);
    if (data.res == "1") {
      showMsg(data.msg, 1);
      setTimeout(function () {
        location.reload();
      }, 3000);
    } else {
      showMsg(data.errmsg, 0);
      return;
    }
  });
  // backend error when check if an OrderProduct obj has review
  $(".review").submit(async function (event) {
    event.preventDefault();
    let star = parseInt($(this).find("select").val());
    if (!(star in [1, 2, 3, 4, 5])) {
      showMsg("Please select a rating star");
      return;
    }
    let orderProductId = $(this).prop("id");
    let comment = $(this).find("textarea").val();
    console.log(comment, star, orderProductId);
    const res = await fetch("/order/comment/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        order_product_id: orderProductId,
        star: star,
        comment: comment,
      }),
    });
    let data = await res.json();
    if (data.res == "1") {
      $(this).find("textarea").prop("disabled");
      $(this).find("button").prop("disabled");
      showMsg(data.msg, 1);
    } else {
      showMsg(data.errmsg, 0);
      // location.reload();
    }
  });
});
