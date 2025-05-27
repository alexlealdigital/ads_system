<div class="row">
    <div class="col-12 mb-4">
        <div class="card metric-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="card-title"><i class="bi bi-image me-2"></i>Detalhes dos Banners</h5>
                    <a href="/add-banner" class="btn btn-primary btn-sm"><i class="bi bi-plus-circle me-1"></i>Adicionar Banner</a>
                </div>

                <div class="debug-marker">DEBUG HTML: Iniciando lista de banners. Ads Count: {{ metrics.banner.ads|length }}</div>
                {% if metrics.banner.ads and metrics.banner.ads|length > 0 %}
                    {% for ad in metrics.banner.ads %}
                    <div style="border: 2px solid red; padding: 10px; margin-bottom: 10px; background-color: #f0f0f0;">
                        <p><strong>Anúncio #{{ loop.index }}</strong></p>
                        <p>ID: {{ ad.id }}</p>
                        <p>Título: {{ ad.title }}</p>
                        <p>
                            <a href="/edit-banner/{{ ad.id }}" style="background-color: green; color: white; padding: 5px; text-decoration: none;">EDITAR</a>
                            <form action="/delete-banner/{{ ad.id }}" method="POST" style="display:inline; margin-left: 10px;" onsubmit="return confirm('Tem certeza que deseja deletar este banner?');">
                                <button type="submit" style="background-color: red; color: white; padding: 5px;">DELETAR</button>
                            </form>
                        </p>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="debug-marker">DEBUG HTML: Lista de banners vazia.</div>
                    <div class="text-center py-3">
                        <p class="text-muted">Nenhum banner cadastrado.</p>
                    </div>
                {% endif %}
                <div class="debug-marker">DEBUG HTML: Fim da lista de banners.</div>
            </div>
        </div>
    </div>
    <div class="col-12 mb-4">
        <div class="card metric-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="card-title"><i class="bi bi-phone me-2"></i>Detalhes dos Anúncios Tela Cheia</h5>
                    <a href="/add-fullscreen" class="btn btn-primary btn-sm"><i class="bi bi-plus-circle me-1"></i>Adicionar Anúncio</a>
                </div>

                <div class="debug-marker">DEBUG HTML: Iniciando lista de fullscreen. Ads Count: {{ metrics.fullscreen.ads|length }}</div>
                {% if metrics.fullscreen.ads and metrics.fullscreen.ads|length > 0 %}
                    {% for ad in metrics.fullscreen.ads %}
                    <div style="border: 2px solid blue; padding: 10px; margin-bottom: 10px; background-color: #f0f0f0;">
                        <p><strong>Anúncio Tela Cheia #{{ loop.index }}</strong></p>
                        <p>ID: {{ ad.id }}</p>
                        <p>Título: {{ ad.title }}</p>
                        <p>
                            <a href="/edit-fullscreen/{{ ad.id }}" style="background-color: green; color: white; padding: 5px; text-decoration: none;">EDITAR</a>
                            <form action="/delete-fullscreen/{{ ad.id }}" method="POST" style="display:inline; margin-left: 10px;" onsubmit="return confirm('Tem certeza que deseja deletar este anúncio?');">
                                <button type="submit" style="background-color: red; color: white; padding: 5px;">DELETAR</button>
                            </form>
                        </p>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="debug-marker">DEBUG HTML: Lista de fullscreen vazia.</div>
                    <div class="text-center py-3">
                        <p class="text-muted">Nenhum anúncio de tela cheia cadastrado.</p>
                    </div>
                {% endif %}
                <div class="debug-marker">DEBUG HTML: Fim da lista de fullscreen.</div>
            </div>
        </div>
    </div>
</div>
