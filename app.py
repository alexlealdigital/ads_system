<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Anúncios</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.0/font/bootstrap-icons.css">
    <style>
        body { 
            background-color: #f8f9fa; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .metric-card {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .banner-bg { 
            background-color: #e3f2fd; 
        }
        
        .fullscreen-bg { 
            background-color: #f0e6ff; 
        }
        
        .chart-container { 
            height: 300px; 
            margin-bottom: 20px; 
            background-color: #fff; 
            padding: 15px;
            border-radius: 5px;
        }

        .ad-list-item-wrapper {
            border: 3px solid red !important;
            margin-bottom: 15px;
            padding: 12px;
            background-color: yellow !important;
            overflow: visible !important;
            min-height: 60px;
            position: relative !important;
            z-index: 1000 !important;
        }
        
        .ad-list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            border: 2px dashed green !important;
            background-color: cyan !important;
            font-size: 16px !important;
            color: black !important;
        }
        
        .ad-list-item:last-child { 
            border-bottom: none; 
        }
        
        .ad-actions { 
            display: flex; 
            gap: 10px;
            flex-shrink: 0;
            border: 2px dotted purple !important;
            background-color: magenta !important;
        }
        
        .btn-edit {
            background-color: white !important; 
            color: black !important; 
            border-radius: 50%;
            width: 36px; 
            height: 36px; 
            padding: 0; 
            display: inline-flex;
            align-items: center; 
            justify-content: center;
            border: 1px solid black !important;
            font-size: 20px !important;
        }
        
        .btn-delete {
            background-color: white !important;
            color: black !important;
            border-radius: 50%;
            width: 36px; 
            height: 36px; 
            padding: 0; 
            display: inline-flex;
            align-items: center; 
            justify-content: center;
            border: 1px solid black !important;
            font-size: 20px !important;
        }
        
        .debug-marker { 
            background-color: #fff0b3; 
            color: #333; 
            padding: 8px; 
            margin: 8px 0; 
            border: 1px solid #ffc107; 
            font-size: 0.9em; 
            border-radius: 4px;
        }
        
        @media (max-width: 768px) {
            .ad-list-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .ad-actions {
                align-self: flex-end;
            }
            
            .chart-container {
                height: 250px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">Dashboard de Anúncios</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/add-banner">
                            <i class="bi bi-plus-circle me-1"></i>Adicionar Banner
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/add-fullscreen">
                            <i class="bi bi-fullscreen me-1"></i>Anúncio Tela Cheia
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="row mb-4">
            <div class="col-12">
                <h1 class="display-5 mb-3">Métricas de Desempenho</h1>
                <p class="lead text-muted">Visualize o desempenho dos seus anúncios em tempo real</p>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-6 mb-4">
                <div class="card metric-card banner-bg h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="bi bi-image me-2"></i>Banners (360×47px)
                        </h5>
                        <div class="row mt-4">
                            <div class="col-md-4 text-center">
                                <h3>{{ metrics.banner.ads_count }}</h3>
                                <p class="text-muted">Total de Anúncios</p>
                            </div>
                            <div class="col-md-4 text-center">
                                <h3>{{ metrics.banner.total_impressions }}</h3>
                                <p class="text-muted">Impressões</p>
                            </div>
                            <div class="col-md-4 text-center">
                                <h3>{{ metrics.banner.ctr }}%</h3>
                                <p class="text-muted">Taxa de Cliques</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-6 mb-4">
                <div class="card metric-card fullscreen-bg h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="bi bi-phone me-2"></i>Tela Cheia (360×640px)
                        </h5>
                        <div class="row mt-4">
                            <div class="col-md-4 text-center">
                                <h3>{{ metrics.fullscreen.ads_count }}</h3>
                                <p class="text-muted">Total de Anúncios</p>
                            </div>
                            <div class="col-md-4 text-center">
                                <h3>{{ metrics.fullscreen.total_impressions }}</h3>
                                <p class="text-muted">Impressões</p>
                            </div>
                            <div class="col-md-4 text-center">
                                <h3>{{ metrics.fullscreen.ctr }}%</h3>
                                <p class="text-muted">Taxa de Cliques</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-6 mb-4">
                <div class="card metric-card h-100">
                    <div class="card-body">
                        <h5 class="card-title mb-3">
                            <i class="bi bi-bar-chart-line me-2"></i>Desempenho de Banners
                        </h5>
                        <div class="chart-container">
                            <canvas id="bannerChart" aria-label="Gráfico de desempenho de banners" role="img"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 mb-4">
                <div class="card metric-card h-100">
                    <div class="card-body">
                        <h5 class="card-title mb-3">
                            <i class="bi bi-bar-chart-line me-2"></i>Desempenho de Anúncios Tela Cheia
                        </h5>
                        <div class="chart-container">
                            <canvas id="fullscreenChart" aria-label="Gráfico de desempenho de anúncios de tela cheia" role="img"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12 mb-4">
                <div class="card metric-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="card-title">
                                <i class="bi bi-image me-2"></i>Detalhes dos Banners
                            </h5>
                            <a href="/add-banner" class="btn btn-primary btn-sm">
                                <i class="bi bi-plus-circle me-1"></i>Adicionar Banner
                            </a>
                        </div>
                        
                        <div class="debug-marker">DEBUG HTML: Iniciando lista de banners. Número de ads: {{ metrics.banner.ads|length }}</div>
                        <div class="debug-marker">DEBUG HTML: metrics.banner.ads existe? {% if metrics.banner.ads is defined %}SIM{% else %}NÃO{% endif %}</div>
                        <div class="debug-marker">DEBUG HTML: metrics.banner.ads é uma lista? {% if metrics.banner.ads is iterable and metrics.banner.ads is not string and metrics.banner.ads is not mapping %}SIM{% else %}NÃO{% endif %}</div>
                        
                        <div class="list-group">
                            {% if metrics.banner.ads and metrics.banner.ads|length > 0 %}
                                {% for ad in metrics.banner.ads %}
                                <div class="debug-marker" style="margin-left: 20px;">
                                    DEBUG HTML (dentro do loop banner): ID {{ ad.id if ad.id is defined else 'N/A' }}, Título: {{ ad.title if ad.title is defined else 'N/A' }}
                                </div>
                                <div class="ad-list-item-wrapper">
                                    <div class="ad-list-item">
                                        <div>
                                            <strong>{{ loop.index }}.</strong> {{ ad.title }}
                                        </div>
                                        <div class="ad-actions">
                                            <a href="/edit-banner/{{ ad.id }}" class="btn btn-edit" aria-label="Editar anúncio {{ ad.title }}">
                                                <i class="bi bi-pencil-fill"></i>
                                            </a>
                                            <form action="/delete-banner/{{ ad.id }}" method="POST" style="display:inline;" onsubmit="return confirm('Tem certeza que deseja deletar este banner?');">
                                                <button type="submit" class="btn btn-delete" aria-label="Deletar anúncio {{ ad.title }}">
                                                    <i class="bi bi-trash-fill"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div class="debug-marker">DEBUG HTML: A lista de banners está vazia ou não é uma lista iterável.</div>
                                <div class="text-center py-3">
                                    <p class="text-muted">Nenhum banner cadastrado.</p>
                                </div>
                            {% endif %}
                        </div>
                        <div class="debug-marker">DEBUG HTML: Fim da lista de banners.</div>
                    </div>
                </div>
            </div>

            <div class="col-12 mb-4">
                <div class="card metric-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="card-title">
                                <i class="bi bi-phone me-2"></i>Detalhes dos Anúncios Tela Cheia
                            </h5>
                            <a href="/add-fullscreen" class="btn btn-primary btn-sm">
                                <i class="bi bi-plus-circle me-1"></i>Adicionar Anúncio
                            </a>
                        </div>
                        
                        <div class="debug-marker">DEBUG HTML: Iniciando lista de anúncios de tela cheia. Número de ads: {{ metrics.fullscreen.ads|length }}</div>
                        <div class="debug-marker">DEBUG HTML: metrics.fullscreen.ads existe? {% if metrics.fullscreen.ads is defined %}SIM{% else %}NÃO{% endif %}</div>
                        <div class="debug-marker">DEBUG HTML: metrics.fullscreen.ads é uma lista? {% if metrics.fullscreen.ads is iterable and metrics.fullscreen.ads is not string and metrics.fullscreen.ads is not mapping %}SIM{% else %}NÃO{% endif %}</div>

                        <div class="list-group">
                           {% if metrics.fullscreen.ads and metrics.fullscreen.ads|length > 0 %}
                                {% for ad in metrics.fullscreen.ads %}
                                <div class="debug-marker" style="margin-left: 20px;">
                                    DEBUG HTML (dentro do loop fullscreen): ID {{ ad.id if ad.id is defined else 'N/A' }}, Título: {{ ad.title if ad.title is defined else 'N/A' }}
                                </div>
                                <div class="ad-list-item-wrapper">
                                    <div class="ad-list-item">
                                        <div>
                                            <strong>{{ loop.index }}.</strong> {{ ad.title }}
                                        </div>
                                        <div class="ad-actions">
                                            <a href="/edit-fullscreen/{{ ad.id }}" class="btn btn-edit" aria-label="Editar anúncio {{ ad.title }}">
                                                <i class="bi bi-pencil-fill"></i>
                                            </a>
                                            <form action="/delete-fullscreen/{{ ad.id }}" method="POST" style="display:inline;" onsubmit="return confirm('Tem certeza que deseja deletar este anúncio?');">
                                                <button type="submit" class="btn btn-delete" aria-label="Deletar anúncio {{ ad.title }}">
                                                    <i class="bi bi-trash-fill"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div class="debug-marker">DEBUG HTML: A lista de anúncios de tela cheia está vazia ou não é uma lista iterável.</div>
                                <div class="text-center py-3">
                                    <p class="text-muted">Nenhum anúncio de tela cheia cadastrado.</p>
                                </div>
                            {% endif %}
                        </div>
                         <div class="debug-marker">DEBUG HTML: Fim da lista de anúncios de tela cheia.</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        console.log("--- DEBUG JS: Script principal do dashboard.html iniciado ---");

        function getSafeArray(dataFromJinja) {
            if (Array.isArray(dataFromJinja)) {
                return dataFromJinja;
            }
            if (typeof dataFromJinja === 'string') {
                try {
                    const parsed = JSON.parse(dataFromJinja);
                    return Array.isArray(parsed) ? parsed : [];
                } catch (e) {
                    console.warn("DEBUG JS: Falha ao fazer parse de dataFromJinja como JSON (getSafeArray), retornando array vazio. Data:", dataFromJinja, "Erro:", e);
                    return [];
                }
            }
            console.warn("DEBUG JS: dataFromJinja não é array nem string JSON (getSafeArray), retornando array vazio. Data:", dataFromJinja);
            return [];
        }

        function getAttributeFromArray(arr, attribute, defaultValueArg) {
            const defaultValue = defaultValueArg !== undefined ? defaultValueArg : (attribute === 'title' ? 'Título N/A' : 0);
            if (!Array.isArray(arr)) {
                 console.warn(`DEBUG JS: Input para getAttributeFromArray (atributo '${attribute}') não é um array. Recebido:`, arr);
                return [];
            }
            return arr.map(item => (item && typeof item === 'object' && item[attribute] !== undefined) ? item[attribute] : defaultValue);
        }

        const rawBannerAds = {{ metrics.banner.ads | default([]) | tojson | safe }};
        const rawFullscreenAds = {{ metrics.fullscreen.ads | default([]) | tojson | safe }};

        console.log("DEBUG JS: rawBannerAds (do Jinja):", typeof rawBannerAds, JSON.parse(JSON.stringify(rawBannerAds)));
        console.log("DEBUG JS: rawFullscreenAds (do Jinja):", typeof rawFullscreenAds, JSON.parse(JSON.stringify(rawFullscreenAds)));

        const bannerAds = getSafeArray(rawBannerAds);
        const fullscreenAds = getSafeArray(rawFullscreenAds);

        console.log("DEBUG JS: bannerAds (após getSafeArray):", JSON.parse(JSON.stringify(bannerAds)));
        console.log("DEBUG JS: fullscreenAds (após getSafeArray):", JSON.parse(JSON.stringify(fullscreenAds)));

        const bannerData = {
            labels: getAttributeFromArray(bannerAds, 'title'),
            datasets: [
                {
                    label: 'Impressões',
                    data: getAttributeFromArray(bannerAds, 'impressions'),
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Cliques',
                    data: getAttributeFromArray(bannerAds, 'clicks'),
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        };

        const fullscreenData = {
            labels: getAttributeFromArray(fullscreenAds, 'title'),
            datasets: [
                {
                    label: 'Impressões',
                    data: getAttributeFromArray(fullscreenAds, 'impressions'),
                    backgroundColor: 'rgba(153, 102, 255, 0.7)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Cliques',
                    data: getAttributeFromArray(fullscreenAds, 'clicks'),
                    backgroundColor: 'rgba(255, 159, 64, 0.7)',
                    borderColor: 'rgba(255, 159, 64, 1)',
                    borderWidth: 1
                }
            ]
        };

        console.log("DEBUG JS: Dados FINAIS para o gráfico de Banners:", JSON.parse(JSON.stringify(bannerData)));
        console.log("DEBUG JS: Dados FINAIS para o gráfico de Tela Cheia:", JSON.parse(JSON.stringify(fullscreenData)));

        const chartConfig = {
            type: 'bar',
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        ticks: { stepSize: 1 } 
                    } 
                },
                plugins: { 
                    legend: {
                        position: 'top',
                    },
                    tooltip: { 
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            }
        };

        window.addEventListener('load', function() {
            console.log("--- DEBUG JS: Evento window.load disparado. Inicializando gráficos. ---");
            
            try {
                if (typeof Chart === 'undefined') {
                    console.error("DEBUG_ERROR: Chart.js NÃO ESTÁ DEFINIDO. Verifique se o script <script src='https://cdn.jsdelivr.net/npm/chart.js'></script> foi carregado ANTES deste script e se não há erros de rede.");
                    return;
                }

                if (document.getElementById('bannerChart')) {
                    const bannerCtx = document.getElementById('bannerChart').getContext('2d');
                    if (bannerCtx) {
                        console.log("DEBUG JS: Contexto do gráfico de banner (bannerCtx) encontrado. Criando gráfico.");
                        new Chart(bannerCtx, { ...chartConfig, data: bannerData });
                    } else {
                        console.error("DEBUG_ERROR: Falha ao obter contexto 2D para 'bannerChart'.");
                    }
                } else {
                    console.warn("DEBUG_WARN: Elemento canvas 'bannerChart' não encontrado no DOM.");
                }
                
                if (document.getElementById('fullscreenChart')) {
                    const fullscreenCtx = document.getElementById('fullscreenChart').getContext('2d');
                    if (fullscreenCtx) {
                        console.log("DEBUG JS: Contexto do gráfico de tela cheia (fullscreenCtx) encontrado. Criando gráfico.");
                        new Chart(fullscreenCtx, { ...chartConfig, data: fullscreenData });
                    } else {
                        console.error("DEBUG_ERROR: Falha ao obter contexto 2D para 'fullscreenChart'.");
                    }
                } else {
                    console.warn("DEBUG_WARN: Elemento canvas 'fullscreenChart' não encontrado no DOM.");
                }
            } catch (error) {
                console.error("DEBUG_ERROR: Erro ao inicializar os gráficos:", error);
                const chartContainers = document.querySelectorAll('.chart-container');
                chartContainers.forEach(container => {
                    container.innerHTML = '<p class="text-danger text-center mt-3">Erro ao carregar gráfico.</p>';
                });
            }
        });
    </script>
</body>
</html>
