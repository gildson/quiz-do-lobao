# -*- coding: utf-8 -*-
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask.ext.login import LoginManager, current_user, login_user, logout_user, login_required
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from app import app, db, forms
from app.models import Usuario, Questao, Partida,PartidaResposta
from simplejson import dumps
import hashlib

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'


def get_questao(partida_id_atual=0):
	partidas_resposta = aliased(PartidaResposta)
	questao = db.session.query(Questao) \
		.outerjoin((partidas_resposta, and_(partidas_resposta.questao_id==Questao._id, partidas_resposta.partida_id==partida_id_atual))) \
		.filter(and_(partidas_resposta._id == None)) \
		.order_by(func.random()) \
		.first()
	return questao

def resposta_is_valid(resposta):
	return resposta in ['a', 'b', 'c', 'd', 'e']

@lm.user_loader
def load_user(id):
	return db.session.query(Usuario).filter_by(_id=id).first()

@app.route('/')
@login_required
def home():
	'''
	partidas = db.session.query(Partida).all()
	for p in partidas:
		print('%d - %d - %d' % (p._id, p.usuario_id, p.questao_atual))
		for r in db.session.query(PartidaResposta).filter_by(partida_id=p._id).all():
			print('%d - %s - %d' % (r._id, r.alternativa_respondida, r.acertou))

	questoes = [get_questao()]

	if questoes:
		for questao in questoes:
			print('%d - %s - %s' % (questao._id, questao.enunciado, questao.alternativa_selecionada))
	'''
	return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = forms.UsuarioLoginForm()

	if form.validate_on_submit():
		usuario = db.session.query(Usuario).filter_by(usuario=form.usuario.data.lower(), senha=hashlib.md5(form.senha.data.encode('utf-8')).hexdigest()).first()
		if usuario:
			login_user(usuario)
		else:
			flash('Usuário ou Senha inválidos.', 'login')

	if not current_user.is_anonymous() and current_user.is_authenticated():
		return redirect( url_for('home') )

	return render_template('usuario/login.html', form=form)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
	form = forms.UsuarioRegistroForm()

	if form.validate_on_submit():
		usuario = db.session.query(Usuario).filter_by(usuario=form.usuario.data.lower()).first()
		email = db.session.query(Usuario).filter_by(email=form.email.data.lower()).first()

		if usuario:
			flash('Usuário informado já existe.', 'registro')

		if email:
			flash('E-mail informado já esta sendo utilizado.', 'registro')

		if not (usuario or email):
			usuario = Usuario(form.usuario.data, form.email.data, form.senha.data)
			db.session.add(usuario)
			db.session.commit()
			if usuario:
				login_user(usuario)

	if not current_user.is_anonymous() and current_user.is_authenticated():
		return redirect( url_for('home') )

	return render_template('usuario/registro.html', form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect( url_for('login') )

@app.route('/questao')
@login_required
def questao():
	questoes = db.session.query(Questao).all()
	n = len(questoes)
	return render_template('/questao/listar.html', questoes=questoes)

@app.route('/questao/novo', methods=['GET', 'POST'])
@login_required
def questao_novo():
	form = forms.QuestaoForm()
	
	if form.validate_on_submit():
		
		questao = Questao(form.enunciado.data, form.alternativa_a.data, form.alternativa_b.data, form.alternativa_c.data, \
			 form.alternativa_d.data, form.alternativa_e.data, form.alternativa_selecionada.data, current_user)
		db.session.add(questao)
		db.session.commit()
		
		flash('Questão cadastrada com sucesso!')
		return redirect( url_for('questao'))
		
	return render_template('/questao/novo.html', form=form)

@app.route('/questao/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def questao_editar(id):
	form = forms.QuestaoForm()

	if id:
		questao = db.session.query(Questao).filter_by(_id=id).first()
		if questao:
			if form.validate_on_submit():
				questao.init_from_QuestaoForm(form)
				db.session.commit()
				return redirect( url_for('questao') )
				
			if request.method == 'GET':
				form.init_from_Questao(questao)
			
			return render_template('/questao/editar.html', form=form, _id=questao._id)

		flash('A questão solicitada não existe ou não está mais disponível.')

	return redirect( url_for('questao') )

''' depois finalizar decorator para generalizar validacao inicial das rotas
@login_required
def login_usuario_partida_required(func):
	def route(*args, **kwargs):
		usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()

		if usuario:
			partida = db.session.query(Partida).filter_by(usuario_id=usuario._id, finalizada=False).first()

			return func(partida, *args, **kwargs)

		return func(*args, **kwargs)

	return route
'''

@app.route('/quiz/inicio')
@login_required
def quiz_inicio():
	usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()

	if usuario:
		partida = db.session.query(Partida).filter_by(usuario_id=usuario._id, finalizada=False).first()

		return render_template('quiz/inicio.html', continuar=partida)

	return 'Usuário não encontrado.'

@app.route('/quiz/novo')
@login_required
def quiz_novo():
	usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()

	if usuario:
		partida = db.session.query(Partida).filter_by(usuario_id=usuario._id, finalizada=False).first()

		# se o usuario ja tem alguma partida em aberto
		if partida:
			partida.finalizada = True
			db.session.commit()

		# obtem uma questao que ainda nao foi respondida pelo usuario nessa partida
		questao = get_questao()

		if questao:
			partida = Partida(usuario._id, questao._id)
			db.session.add(partida)
			db.session.commit()

			return redirect( url_for('quiz') )

		return 'Não foram encontradas questões para responder.'

	return 'Usuário não encontrado'

@app.route('/quiz')
@login_required
def quiz():
	usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()

	if usuario:
		partida = db.session.query(Partida).filter_by(usuario_id=usuario._id, finalizada=False).first()
		
		if partida:
			return render_template('quiz/quiz.html')
		
		return redirect( url_for('quiz_inicio') )

	return 'Usuário não encontrado'

@app.route('/quiz/rodada', methods=['POST'])
@login_required
def quiz_rodada():
	usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()

	if usuario:
		partida = db.session.query(Partida).filter_by(usuario_id=usuario._id, finalizada=False).first()

		if partida:
			questao = db.session.query(Questao).filter_by(_id=partida.questao_atual).first()

			if questao:
				return jsonify(partida=partida.to_dict(), questao=questao.to_dict())

		return redirect( url_for('quiz_inicio') )
		
	return 'Usuário não encontrado'

@app.route('/quiz/responder', methods=['GET', 'POST'])
@login_required
def quiz_responder():
	resposta = request.form['resposta']

	usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()

	if usuario and resposta_is_valid(resposta):
		partida = db.session.query(Partida).filter_by(usuario_id=usuario._id, finalizada=False).first()

		if partida:
			questao_respondida = db.session.query(Questao).filter_by(_id=partida.questao_atual).first()

			acertou = questao_respondida.alternativa_correta == resposta

			partidas_resposta = PartidaResposta(usuario._id, questao_respondida._id, partida._id, resposta, acertou)
			db.session.add(partidas_resposta)
			db.session.commit()

			if acertou:
				partida.rodada = partida.rodada + 1
				partida.questao_atual = get_questao(partida._id)._id
			else:
				partida.finalizada = True

			db.session.commit()

			return jsonify({'acertou': acertou})

		return 'Partida não encontrada'

	return 'Usuário não encontrado'






#ajustar ta tpda errada ainda
def get_quiz_resultado():
	usr = aliased(Usuario)
	partidas = db.session.query(Partida) \
				.outerjoin((Partida, usr)) \
				.order_by('rodada').filter()
	return partidas

@app.route('/quiz/resultado', methods=['GET', 'POST'])
@login_required
def quiz_resultado():
	usuario = db.session.query(Usuario).filter_by(_id=current_user._id).first()
	posicao_ranking = 1 #get_quiz_resultado()
	if usuario:
		resultado = {'usuario': usuario.usuario, 'posicao_ranking': posicao_ranking,}
		return render_template('/quiz/resultado.html', resultado=resultado)

	return 'Usuário não encontrado'