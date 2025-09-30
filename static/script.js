// Chart.js Pie Chart for dashboard
const ctx = document.getElementById("patientsChart").getContext("2d");
new Chart(ctx, {
  type: "doughnut",
  data: {
    labels: ["New Patients", "Old Patients", "Total Patients"],
    datasets: [
      {
        data: [30, 45, 25],
        backgroundColor: ["#a6c8ff", "#ffc04d", "#005dff"],
        borderWidth: 1,
      },
    ],
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        position: "bottom",
      },
    },
  },
});
