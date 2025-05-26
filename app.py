from flask import Flask, render_template, request, redirect, url_for
import logging

app = Flask(__name__)

# Configuração básica de logging
# Isso fará com que os logs apareçam no console onde você executa o 'flask run' ou 'python app.py'
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Simulação de um "banco de dados" em memória
db = {
    "banners": [],
    "fullscreen_ads": [],
    "next_banner_id": 1,
    "next_fullscreen_id": 1
}

def calculate_ctr(clicks, impressions):
    if impressions == 0:
        return 0.0
    return round((clicks / impressions) * 100, 2)

@app.route('/')
def dashboard():
    app.logger.info("Acessando a rota do Dashboard ('/')")

    # Preparando dados dos Banners
    banner_ads_list = db["banners"]
    total_banner_impressions = sum(ad.get('impressions', 0) for ad in banner_ads_list)
    total_banner_clicks = sum(ad.get('clicks', 0) for ad in banner_ads_list)
    banner_ctr = calculate_ctr(total_banner_clicks, total_banner_impressions)

    metrics_banner = {
        "ads_count": len(banner_ads_list),
        "total_impressions": total_banner_impressions,
        "ctr": banner_ctr,
        "ads": banner_ads_list  # Esta é a lista que o template itera
    }
    app.logger.debug(f"Métricas de Banner preparadas: {metrics_banner}")

    # Preparando dados dos Anúncios de Tela Cheia
    fullscreen_ads_list = db["fullscreen_ads"]
    total_fullscreen_impressions = sum(ad.get('impressions', 0) for ad in fullscreen_ads_list)
    total_fullscreen_clicks = sum(ad.get('clicks', 0) for ad in fullscreen_ads_list)
    fullscreen_ctr = calculate_ctr(total_fullscreen_clicks, total_fullscreen_impressions)

    metrics_fullscreen = {
        "ads_count": len(fullscreen_ads_list),
        "total_impressions": total_fullscreen_impressions,
        "ctr": fullscreen_ctr,
        "ads": fullscreen_ads_list  # Esta é a lista que o template itera
    }
    app.logger.debug(f"Métricas de Tela Cheia preparadas: {metrics_fullscreen}")

    metrics_data = {
        "banner": metrics_banner,
        "fullscreen": metrics_fullscreen
    }
    app.logger.info(f"Dados finais enviados para o template dashboard.html: {metrics_data}")

    # Renderiza 'dashboard.html' que você já possui
    return render_template('dashboard.html', metrics=metrics_data)

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    app.logger.info(f"Acessando a rota '/add-banner' com o método: {request.method}")
    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            app.logger.info(f"Dados recebidos do formulário de banner: Título='{title}', ImageURL='{imageUrl}', TargetURL='{targetUrl}'")

            new_banner = {
                "id": db["next_banner_id"],
                "title": title,
                "imageUrl": imageUrl,
                "targetUrl": targetUrl,
                "impressions": 0, # Inicializa com 0
                "clicks": 0       # Inicializa com 0
            }
            db["banners"].append(new_banner)
            db["next_banner_id"] += 1
            app.logger.info(f"Novo banner adicionado com sucesso: {new_banner}")
            app.logger.debug(f"Estado atual dos banners no DB: {db['banners']}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao adicionar banner: {e}", exc_info=True)
            # Em um app real, você poderia renderizar uma página de erro ou retornar uma mensagem
            return render_template('error.html', message="Erro ao adicionar o banner.")

    # Renderiza 'add_banner.html' que você já possui
    return render_template('add_banner.html')

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    app.logger.info(f"Acessando a rota '/add-fullscreen' com o método: {request.method}")
    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            app.logger.info(f"Dados recebidos do formulário de tela cheia: Título='{title}', ImageURL='{imageUrl}', TargetURL='{targetUrl}'")

            new_fullscreen_ad = {
                "id": db["next_fullscreen_id"],
                "title": title,
                "imageUrl": imageUrl,
                "targetUrl": targetUrl,
                "impressions": 0, # Inicializa com 0
                "clicks": 0       # Inicializa com 0
            }
            db["fullscreen_ads"].append(new_fullscreen_ad)
            db["next_fullscreen_id"] += 1
            app.logger.info(f"Novo anúncio de tela cheia adicionado com sucesso: {new_fullscreen_ad}")
            app.logger.debug(f"Estado atual dos anúncios de tela cheia no DB: {db['fullscreen_ads']}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao adicionar anúncio de tela cheia: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao adicionar o anúncio de tela cheia.")

    # Renderiza 'add_fullscreen.html' que você já possui
    return render_template('add_fullscreen.html')

# --- Rotas de Edição e Deleção (Exemplo Simplificado) ---
# Você precisará implementar a lógica para encontrar e modificar/remover os itens.

@app.route('/edit-banner/<int:ad_id>', methods=['GET', 'POST'])
def edit_banner(ad_id):
    app.logger.info(f"Acessando a rota '/edit-banner/{ad_id}' com o método: {request.method}")
    banner_to_edit = next((banner for banner in db["banners"] if banner["id"] == ad_id), None)

    if not banner_to_edit:
        app.logger.warning(f"Tentativa de editar banner com ID {ad_id} não encontrado.")
        return render_template('error.html', message=f"Banner com ID {ad_id} não encontrado."), 404

    if request.method == 'POST':
        try:
            banner_to_edit['title'] = request.form['title']
            banner_to_edit['imageUrl'] = request.form['imageUrl']
            banner_to_edit['targetUrl'] = request.form['targetUrl']
            app.logger.info(f"Banner ID {ad_id} atualizado: {banner_to_edit}")
            app.logger.debug(f"Estado atual dos banners no DB após edição: {db['banners']}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao editar banner ID {ad_id}: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao salvar as alterações do banner.")

    app.logger.debug(f"Renderizando formulário de edição para o banner: {banner_to_edit}")
    # Renderiza 'edit_banner.html' que você já possui
    return render_template('edit_banner.html', banner=banner_to_edit)


@app.route('/delete-banner/<int:ad_id>', methods=['POST'])
def delete_banner(ad_id):
    app.logger.info(f"Acessando a rota POST '/delete-banner/{ad_id}'")
    initial_len = len(db["banners"])
    db["banners"] = [banner for banner in db["banners"] if banner["id"] != ad_id]
    if len(db["banners"]) < initial_len:
        app.logger.info(f"Banner com ID {ad_id} deletado com sucesso.")
    else:
        app.logger.warning(f"Tentativa de deletar banner com ID {ad_id}, mas não foi encontrado.")
    app.logger.debug(f"Estado atual dos banners no DB após tentativa de deleção: {db['banners']}")
    return redirect(url_for('dashboard'))

@app.route('/edit-fullscreen/<int:ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    app.logger.info(f"Acessando a rota '/edit-fullscreen/{ad_id}' com o método: {request.method}")
    ad_to_edit = next((ad for ad in db["fullscreen_ads"] if ad["id"] == ad_id), None)

    if not ad_to_edit:
        app.logger.warning(f"Tentativa de editar anúncio de tela cheia com ID {ad_id} não encontrado.")
        return render_template('error.html', message=f"Anúncio de tela cheia com ID {ad_id} não encontrado."), 404

    if request.method == 'POST':
        try:
            ad_to_edit['title'] = request.form['title']
            ad_to_edit['imageUrl'] = request.form['imageUrl']
            ad_to_edit['targetUrl'] = request.form['targetUrl']
            app.logger.info(f"Anúncio de tela cheia ID {ad_id} atualizado: {ad_to_edit}")
            app.logger.debug(f"Estado atual dos anúncios de tela cheia no DB após edição: {db['fullscreen_ads']}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao editar anúncio de tela cheia ID {ad_id}: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao salvar as alterações do anúncio de tela cheia.")

    app.logger.debug(f"Renderizando formulário de edição para o anúncio de tela cheia: {ad_to_edit}")
    # Renderiza 'edit_fullscreen.html' que você já possui
    return render_template('edit_fullscreen.html', ad=ad_to_edit)


@app.route('/delete-fullscreen/<int:ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    app.logger.info(f"Acessando a rota POST '/delete-fullscreen/{ad_id}'")
    initial_len = len(db["fullscreen_ads"])
    db["fullscreen_ads"] = [ad for ad in db["fullscreen_ads"] if ad["id"] != ad_id]
    if len(db["fullscreen_ads"]) < initial_len:
        app.logger.info(f"Anúncio de tela cheia com ID {ad_id} deletado com sucesso.")
    else:
        app.logger.warning(f"Tentativa de deletar anúncio de tela cheia com ID {ad_id}, mas não foi encontrado.")
    app.logger.debug(f"Estado atual dos anúncios de tela cheia no DB após tentativa de deleção: {db['fullscreen_ads']}")
    return redirect(url_for('dashboard'))


# Rota para simular um clique (para fins de teste de CTR, se necessário)
@app.route('/click/banner/<int:ad_id>')
def click_banner(ad_id):
    banner = next((b for b in db["banners"] if b["id"] == ad_id), None)
    if banner:
        banner['clicks'] = banner.get('clicks', 0) + 1
        app.logger.info(f"Clique registrado para banner ID {ad_id}. Total de cliques: {banner['clicks']}")
        # Idealmente, redirecionaria para banner['targetUrl']
        return f"Banner {ad_id} clicado! Redirecionando para {banner['targetUrl']} (simulado)"
    return "Banner não encontrado", 404

@app.route('/impression/banner/<int:ad_id>')
def impression_banner(ad_id):
    banner = next((b for b in db["banners"] if b["id"] == ad_id), None)
    if banner:
        banner['impressions'] = banner.get('impressions', 0) + 1
        app.logger.info(f"Impressão registrada para banner ID {ad_id}. Total de impressões: {banner['impressions']}")
        return f"Impressão para banner {ad_id} registrada!"
    return "Banner não encontrado", 404

# Adicione rotas similares para '/click/fullscreen/<int:ad_id>' e '/impression/fullscreen/<int:ad_id>'


if __name__ == '__main__':
    app.logger.info("Iniciando a aplicação Flask Ad Dashboard.")
    # Não defina app.debug=True aqui se já estiver usando logging extensivo para DEBUG.
    # O modo debug do Flask tem seu próprio reloader e debugger.
    # Para produção, use um servidor WSGI como Gunicorn ou Waitress.
    app.run(host='0.0.0.0', port=5000)
