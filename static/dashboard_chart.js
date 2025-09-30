// Chart.js example for dashboard
window.addEventListener('DOMContentLoaded', function() {
  if (document.getElementById('appointmentsChart')) {
    const ctx = document.getElementById('appointmentsChart').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: window.dashboardLabels || [],
        datasets: [{
          label: 'Appointments',
          data: window.dashboardData || [],
          backgroundColor: [
            '#6a11cb', '#2575fc', '#ff6384', '#36a2eb', '#cc65fe', '#ffce56'
          ],
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'Appointments per Doctor' }
        }
      }
    });
  }
});
