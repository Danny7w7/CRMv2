document.addEventListener("DOMContentLoaded", function () {
    var e = {
        series: [{
            name: "Message",
            data: Object.values(messages),
        }],
        chart: {
            foreColor: "#9ba7b2",
            height: 310,
            type: "area",
            zoom: { enabled: false },
            toolbar: { show: true },
            dropShadow: { enabled: true, top: 3, left: 14, blur: 4, opacity: 0.1 },
        },
        stroke: { width: 5, curve: "smooth" },
        xaxis: { categories: Object.values(dayNames) },
        title: {
            text: "Week's messages",
            align: "left",
            style: { fontSize: "16px", color: "#666" },
        },
        fill: {
            type: "gradient",
            gradient: {
                shade: "light",
                gradientToColors: ["#0d6efd"],
                shadeIntensity: 1,
                type: "vertical",
                opacityFrom: 0.7,
                opacityTo: 0.2,
                stops: [0, 100, 100, 100],
            },
        },
        markers: {
            size: 5,
            colors: ["#0d6efd"],
            strokeColors: "#fff",
            strokeWidth: 2,
            hover: { size: 7 },
        },
        dataLabels: { enabled: false },
        colors: ["#0d6efd"],
        grid: {
            show: true,
            borderColor: 'rgba(0, 0, 0, 0.15)',
            strokeDashArray: 4,
        },
        tooltip: {
            theme: 'dark',
            y: { formatter: function (val) { return val + " items"; } }
        },
    };
    new ApexCharts(document.querySelector("#sms"), e).render();
});
