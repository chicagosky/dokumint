function initCreditChart(canvas, data) {
    var creditChart = echarts.init(canvas);
    let creditOptions = {
        title: {
            show: true,
            text: 'Credit Usage Summary',
        },
        legend: {
            bottom: '1%',
            left: 'center'
        },
        series: [{
            type: 'pie',
            radius: ['60%', '70%'],
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            avoidLabelOverlap: true,
            label: {
                show: true,
                position: 'center'
            },
            labelLine: {
                show: true
            },
            data: [
                { value: data.credits_used, name: 'Used' },
                { value: data.credits_balance, name: 'Available' },
            ],
        }],
      };
    creditChart.setOption(creditOptions);
}

function initProcessingChart(canvas, data) {
    var processChart = echarts.init(canvas);
    let processOptions = {
        title: {
            show: true,
            text: 'Processing Summary',
        },
        xAxis: {
            type: 'category',
            data: ['Receipts', 'Line Items']
        },
        yAxis: {
            type: 'value'
        },
        series: [{
            type: 'bar',
            data: [
                data.receipts, 
                data.line_items
            ],
        }],
      };
      processChart.setOption(processOptions);
}