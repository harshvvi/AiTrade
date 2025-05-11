var PieChart = (function() {

    //
    // Variables
    //

    var $chart = $('#chart-pie');


    //
    // Methods
    //

    // Init chart
    function initChart($chart) {

        // Create chart
        var pieChart = new Chart($chart, {
            type: 'pie',
            data: {
                labels: ['Category A', 'Category B', 'Category C', 'Category D'],
                datasets: [{
                    data: [30, 20, 15, 35],
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4CAF50']
                }]
            }
        });

        // Save to jQuery object
        $chart.data('chart', pieChart);
    }

    // Init chart
    if ($chart.length) {
        initChart($chart);
    }

})();
