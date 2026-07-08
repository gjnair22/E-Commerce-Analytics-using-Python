document.addEventListener('DOMContentLoaded', () => {
    // Initialize icons
    lucide.createIcons();

    // Elements
    const themeToggleBtn = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // Chart instances registry (to destroy/recreate on theme toggle)
    let charts = {};
    let dashboardData = null;

    // Theme toggler
    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        const isLight = document.body.classList.contains('light-mode');
        
        // Toggle icon states
        sunIcon.classList.toggle('hidden', isLight);
        moonIcon.classList.toggle('hidden', !isLight);

        // Update charts with new theme colors
        if (dashboardData) {
            destroyCharts();
            renderCharts(dashboardData);
        }
    });

    // Tab Switching
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Toggle buttons active state
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle tab pane visibility
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === `${targetTab}-tab`) {
                    pane.classList.add('active');
                }
            });
        });
    });

    // Load Dashboard Data
    fetch('dashboard_data.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load JSON dashboard data. Have you run main.py first?');
            }
            return response.json();
        })
        .then(data => {
            dashboardData = data;
            populateKPIs(data.kpis);
            renderCharts(data);
            populateInsights(data.kpis);
        })
        .catch(err => {
            console.error(err);
            alert('Could not load analysis dataset. Please run python main.py first.');
        });

    // Populate KPI Cards
    function populateKPIs(kpis) {
        document.getElementById('kpi-revenue').textContent = `R$ ${(kpis.total_revenue / 1e6).toFixed(2)}M`;
        document.getElementById('kpi-orders').textContent = kpis.total_orders.toLocaleString();
        document.getElementById('kpi-customers').textContent = kpis.total_customers.toLocaleString();
        document.getElementById('kpi-delivery-time').textContent = `${kpis.avg_delivery_time.toFixed(1)} days`;

        document.getElementById('kpi-aov').textContent = `AOV: R$ ${kpis.avg_order_value.toFixed(2)}`;
        document.getElementById('kpi-repeat-rate').textContent = `Repeat Rate: ${kpis.repeat_rate.toFixed(2)}%`;
        document.getElementById('kpi-late-rate').textContent = `Late Rate: ${kpis.late_delivery_rate.toFixed(2)}%`;
    }

    // Populate Dynamic Insights List
    function populateInsights(kpis) {
        const listContainer = document.getElementById('insights-list-container');
        listContainer.innerHTML = ''; // Clear

        const insights = [
            {
                title: "Customer Concentration",
                desc: `Customers are heavily clustered in <strong>${kpis.top_state}</strong>, which accounts for <strong>${kpis.top_state_count.toLocaleString()}</strong> unique customers. Prioritize regional marketing campaigns and optimize logistics hubs in São Paulo to reduce delivery costs.`,
                icon: "users"
            },
            {
                title: "Product Category Revenue Mix",
                desc: `The <strong>'${kpis.top_category}'</strong> category is the highest revenue generator, contributing <strong>R$ ${(kpis.top_category_revenue / 1e6).toFixed(2)}M</strong>. Meanwhile, the highest average unit price is in <strong>'${kpis.highest_avg_price_category}'</strong> (avg. <strong>R$ ${kpis.highest_avg_price.toFixed(2)}</strong> per item).`,
                icon: "package"
            },
            {
                title: "Customer Repeat Purchase Deficit",
                desc: `Olist has a repeat purchase rate of only <strong>${kpis.repeat_rate.toFixed(2)}%</strong>. This indicates the marketplace is highly transactional. Implementing post-purchase marketing campaigns, coupons, or a subscription program is a critical growth lever.`,
                icon: "refresh-cw"
            },
            {
                title: "Payment Methods Analysis",
                desc: `<strong>Credit Card</strong> represents the dominant payment channel, making up <strong>${kpis.credit_card_share.toFixed(1)}%</strong> of transactions. CC purchases are paid in <strong>${kpis.avg_cc_installments.toFixed(1)} installments</strong> on average.`,
                icon: "credit-card"
            },
            {
                title: "Delivery Speed & Satisfaction Risks",
                desc: `Orders take <strong>${kpis.avg_delivery_time.toFixed(1)} days</strong> on average to arrive. The late delivery rate is <strong>${kpis.late_delivery_rate.toFixed(2)}%</strong>. Tracking this rate is vital, as shipment delays are heavily correlated with negative review scores.`,
                icon: "truck"
            }
        ];

        insights.forEach(item => {
            const card = document.createElement('div');
            card.className = 'insight-card';
            card.innerHTML = `
                <div class="insight-icon-container">
                    <i data-lucide="${item.icon}"></i>
                </div>
                <div class="insight-text">
                    <h4>${item.title}</h4>
                    <p>${item.desc}</p>
                </div>
            `;
            listContainer.appendChild(card);
        });

        // Initialize icons inside insights
        lucide.createIcons();
    }

    // Destroy current charts
    function destroyCharts() {
        Object.keys(charts).forEach(key => {
            if (charts[key]) {
                charts[key].destroy();
            }
        });
        charts = {};
    }

    // Render interactive charts using Chart.js
    function renderCharts(data) {
        const isLight = document.body.classList.contains('light-mode');
        
        // Theme-sensitive styling parameters
        const textPrimary = isLight ? '#0f172a' : '#f8fafc';
        const textSecondary = isLight ? '#475569' : '#94a3b8';
        const gridColor = isLight ? 'rgba(148, 163, 184, 0.1)' : 'rgba(148, 163, 184, 0.05)';
        const cardBg = isLight ? '#ffffff' : '#131a2e';

        // Global Chart.js defaults
        Chart.defaults.font.family = "'Outfit', sans-serif";
        Chart.defaults.font.size = 11;
        Chart.defaults.color = textSecondary;
        Chart.defaults.plugins.tooltip.backgroundColor = cardBg;
        Chart.defaults.plugins.tooltip.titleColor = textPrimary;
        Chart.defaults.plugins.tooltip.bodyColor = textSecondary;
        Chart.defaults.plugins.tooltip.borderColor = isLight ? '#cbd5e1' : '#223056';
        Chart.defaults.plugins.tooltip.borderWidth = 1;

        // 1. Line Chart: Monthly Revenue Trend
        const ctxMonthly = document.getElementById('monthlyRevenueChart').getContext('2d');
        const revenueK = data.charts.monthly_revenue.values.map(val => val / 1000);
        
        // Gradient for Line Chart
        const lineGrad = ctxMonthly.createLinearGradient(0, 0, 0, 300);
        lineGrad.addColorStop(0, 'rgba(249, 115, 22, 0.35)');
        lineGrad.addColorStop(1, 'rgba(249, 115, 22, 0.0)');

        charts.monthly = new Chart(ctxMonthly, {
            type: 'line',
            data: {
                labels: data.charts.monthly_revenue.labels,
                datasets: [{
                    label: 'Revenue (Thousands BRL)',
                    data: revenueK,
                    borderColor: '#f97316',
                    borderWidth: 3,
                    fill: true,
                    backgroundColor: lineGrad,
                    tension: 0.3,
                    pointBackgroundColor: '#1e293b',
                    pointBorderColor: '#f97316',
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: '#f97316',
                    pointHoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textSecondary }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textSecondary,
                            callback: (value) => `R$ ${value}k`
                        }
                    }
                }
            }
        });

        // 2. Horizontal Bar: Top Categories
        const ctxCategories = document.getElementById('categoryRevenueChart').getContext('2d');
        const revMillions = data.charts.categories.values.map(val => val / 1e6);
        
        // Gradient for Bar Chart
        const barGradTeal = ctxCategories.createLinearGradient(0, 0, 300, 0);
        barGradTeal.addColorStop(0, '#0d9488');
        barGradTeal.addColorStop(1, '#14b8a6');

        charts.categories = new Chart(ctxCategories, {
            type: 'bar',
            data: {
                labels: data.charts.categories.labels,
                datasets: [{
                    data: revMillions,
                    backgroundColor: barGradTeal,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Revenue: R$ ${context.parsed.x.toFixed(2)}M`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textSecondary,
                            callback: (value) => `R$ ${value}M`
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: textSecondary }
                    }
                }
            }
        });

        // 3. Horizontal Bar: Top States
        const ctxStates = document.getElementById('stateCustomersChart').getContext('2d');
        const barGradPurple = ctxStates.createLinearGradient(0, 0, 300, 0);
        barGradPurple.addColorStop(0, '#6d28d9');
        barGradPurple.addColorStop(1, '#8b5cf6');

        charts.states = new Chart(ctxStates, {
            type: 'bar',
            data: {
                labels: data.charts.states.labels,
                datasets: [{
                    data: data.charts.states.values,
                    backgroundColor: barGradPurple,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Customers: ${context.parsed.x.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textSecondary }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: textSecondary }
                    }
                }
            }
        });

        // 4. Doughnut Chart: Payment Types
        const ctxPayment = document.getElementById('paymentTypesChart').getContext('2d');
        charts.payments = new Chart(ctxPayment, {
            type: 'doughnut',
            data: {
                labels: data.charts.payment_types.labels,
                datasets: [{
                    data: data.charts.payment_types.values,
                    backgroundColor: ['#8b5cf6', '#3b82f6', '#14b8a6', '#f97316', '#e2e8f0'],
                    borderWidth: isLight ? 2 : 3,
                    borderColor: cardBg,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: textPrimary,
                            boxWidth: 12,
                            padding: 12
                        }
                    }
                }
            }
        });

        // 5. Vertical Bar Chart: Delivery Lead Time Bins
        const ctxDelivery = document.getElementById('deliveryDistributionChart').getContext('2d');
        charts.delivery = new Chart(ctxDelivery, {
            type: 'bar',
            data: {
                labels: data.charts.delivery_times.labels,
                datasets: [{
                    data: data.charts.delivery_times.values,
                    backgroundColor: 'rgba(139, 92, 246, 0.75)',
                    hoverBackgroundColor: '#8b5cf6',
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: textSecondary,
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 12
                        }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textSecondary }
                    }
                }
            }
        });
    }
});
