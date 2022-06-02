import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.core import serializers
import json
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test

from .models import Cliente, Produto, Categoria, Rating, Compras, Comentarios


# --------------------- Base / Login ---------------------

def home(request):
    lista_produto = Produto.objects.all()
    context = {'lista_produto': lista_produto}
    return render(request, 'loja/home.html', context)


def index(request):
    try:
        categoria_id = request.session['categoria']
    except KeyError:
        request.session['categoria'] = 0
        categoria_id = request.session['categoria']
    lista_categoria = Categoria.objects.all()
    if categoria_id == 0:
        lista_produto = Produto.objects.all()
        context = {'lista_categoria': lista_categoria, 'lista_produto': lista_produto}
    else:
        categoria = get_object_or_404(Categoria, pk=categoria_id)
        lista_produto = categoria.produto_set.all()
        context = {'lista_produto': lista_produto, 'categoria': categoria, 'lista_categoria': lista_categoria}
    return render(request, 'loja/index.html', context)


def util(request,categoria_id):
    request.session['categoria'] = categoria_id
    return HttpResponseRedirect(reverse('loja:index'))


def loginview(request):
    username = request.POST['username']
    password = request.POST['pass']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        request.session['lista_carrinho'] = []
        return HttpResponseRedirect(reverse('loja:home'))
    else:
        return HttpResponseRedirect(reverse('loja:home'))


def logoutview(request):
    logout(request)
    return HttpResponseRedirect(reverse('loja:home'))


def registaruser(request):
    return render(request, 'loja/registaruser.html')


def registo(request):
    username = request.POST['username']
    password = request.POST['pass']
    email = request.POST.get('email')
    curso = request.POST['curso']
    user = User.objects.create_user(username, email, password)
    user.save()
    if bool(request.FILES.get('myfile', False)):
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)[5:]  # remover /loja
        cliente = Cliente(user=user, curso=curso, foto=uploaded_file_url)
    else:
        cliente = Cliente(user=user, curso=curso)
    cliente.save()
    login(request, user)
    return HttpResponseRedirect(reverse('loja:home'))


def perfil(request):
    cliente = Cliente.objects.filter(user=request.user)
    return render(request, 'loja/perfil.html', {'cliente': cliente})


def editar_user(request):
    return render(request, 'loja/editar_user.html')


def update_user(request):
    request.user.cliente.user.username = request.POST['username']
    request.user.cliente.user.email = request.POST['email']
    request.user.cliente.curso = request.POST['curso']
    if bool(request.FILES.get('myfile', False)):
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)[5:]  # remover /loja
        request.user.cliente.foto = uploaded_file_url
    request.user.cliente.save()

    return HttpResponseRedirect(reverse('loja:perfil'))


# --------------------- Produto ---------------------

def criar_produto(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    context = {'categoria': categoria}
    return render(request, 'loja/criar_produto.html', context)


def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    lista_categoria = Categoria.objects.all()
    context = {'produto': produto, 'lista_categoria': lista_categoria, 'categoria': produto.categoria}
    return render(request, 'loja/editar_produto.html', context)


def apagar_produto(request, produto_id):
    record = Produto.objects.get(id=produto_id)
    record.delete()
    return HttpResponseRedirect(reverse('loja:index'))


def detalhe_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    total = 0
    count = 0
    already_voted = False
    for rate in Rating.objects.all():
        if rate.produto == produto:
            total += rate.rate
            count +=1
            try:
                if request.user.cliente == rate.cliente:
                    already_voted = True
            except:
                print()
    if request.user.is_superuser:
        already_voted = True
    if not request.user.is_authenticated:
        already_voted = True

    media, media_round, px_star = percentagem_votos(count,total)

    return render(request, 'loja/detalhe_produto.html', {'produto': produto, 'media':media, 'mediaRound': media_round, 'count':count, 'already_voted':already_voted, 'px_star':px_star})


def percentagem_votos(count, total):
    if count > 0:
        media = round(total / count, 2)
        i, d = divmod(round(total / count, 2), 1)
        if d == 0:
            mediaRound = i - 1
            px_star = 30
        else:
            mediaRound = i
            px_star = round(d * 30,0)

    else:
        px_star = 30
        mediaRound = 0
        media = 0
    return media, mediaRound, px_star


def rate_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    rate = request.POST['inlineRadioOptions']
    rating = Rating(produto=produto, cliente=request.user.cliente, rate=int(rate))
    rating.save()
    return HttpResponseRedirect(reverse('loja:detalhe_produto', args=(produto_id,)))


def comentarios_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    lista_comentarios = []
    already_comment = False
    lista_rates = produto.rating_set.all()
    for comentario in Comentarios.objects.all():
        if comentario.produto == produto:
            lista_comentarios.append(comentario)
            try:
                if request.user.cliente == comentario.cliente:
                    already_comment = True
            except:
                print()
    if request.user.is_superuser:
        already_comment = True
    if not request.user.is_authenticated:
        already_comment = True
    return render(request, 'loja/comentarios_produto.html', {'lista_comentarios': lista_comentarios, 'already_comment':already_comment,'produto_id':produto_id ,'lista_rates':lista_rates})


def comentar_produto(request, produto_id):
    return render(request, 'loja/comentar_produto.html', {'produto_id':produto_id })


def criar_comentario(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    c = request.POST['comment']
    if len(c) <= 100:
        comment = Comentarios(produto=produto, cliente=request.user.cliente, comentario=c)
        comment.save()
    return HttpResponseRedirect(reverse('loja:comentarios_produto', args=(produto_id,)))


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comentarios, pk=comment_id)
    produto_id = comment.produto.id
    comment.delete()
    return HttpResponseRedirect(reverse('loja:comentarios_produto', args=(produto_id,)))


def update_produto(request, produto_id):
    categoria_id = request.POST['categoria_select']
    produto = get_object_or_404(Produto, pk=produto_id)
    cat = get_object_or_404(Categoria, pk=categoria_id)
    produto.produto_nome = request.POST['produto_nome']
    produto.produto_texto = request.POST['produto_texto']
    produto.preco_data = request.POST['preco_data']
    produto.categoria = cat
    if bool(request.FILES.get('produto_file', False)):
        myfile = request.FILES['produto_file']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)[5:]  # remover /loja
        produto.foto = uploaded_file_url
    produto.save()

    return HttpResponseRedirect(reverse('loja:index'))


def novo_produto(request, categoria_id):
    produto_nome = request.POST['produto_nome']
    produto_texto = request.POST['produto_texto']
    preco_data = request.POST['preco_data']
    cat = get_object_or_404(Categoria, pk=categoria_id)
    if bool(request.FILES.get('produto_file', False)):
        myfile = request.FILES['produto_file']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)[5:]  # remover /loja
        print(uploaded_file_url)
        produto = Produto(produto_nome=produto_nome, produto_texto=produto_texto, preco_data=preco_data,
                          categoria=cat, foto=uploaded_file_url)

    else:
        produto = Produto(produto_nome=produto_nome, produto_texto=produto_texto, preco_data=preco_data,
                          categoria=cat)
    produto.save()

    return HttpResponseRedirect(reverse('loja:index'))


# --------------------- Categoria ---------------------

def criar_categoria(request):
    return render(request, 'loja/criar_categoria.html')


def apagar_categoria(request, categoria_id):
    record = Categoria.objects.get(id=categoria_id)
    lista_categoria = Categoria.objects.all()
    lista_produto = []
    for p in Produto.objects.all():
        if p.categoria_id == categoria_id:
            lista_produto.append(p)
    context = {'lista_produto': lista_produto, 'categoria': record, 'lista_categoria': lista_categoria,
               'delete_category_error':"Category cannot be removed once it features products, delete all products or change their category."}
    for p in Produto.objects.all():
        if p.categoria_id == categoria_id:
            return render(request, 'loja/index.html', context)
    record.delete()
    return HttpResponseRedirect(reverse('loja:util', args=(0,)))


def nova_categoria(request):
    categoria_nome = request.POST['categoria_nome']
    categoria = Categoria(categoria_nome=categoria_nome)
    categoria.save()
    return HttpResponseRedirect(reverse('loja:index'))


def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    context = {'categoria': categoria}
    return render(request, 'loja/editar_categoria.html', context)


def update_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    categoria.categoria_nome = request.POST['categoria_nome']
    categoria.save()
    return HttpResponseRedirect(reverse('loja:index'))


def procurar_produto(request):
    produto_nome = request.POST['produto_procura']
    lista_categoria = Categoria.objects.all()
    if produto_nome:
        lista = []
        for p in Produto.objects.all():
            if produto_nome in p.produto_nome:
                lista.append(p)
        context = {'lista_produto': lista, 'lista_categoria':lista_categoria}
        return render(request, 'loja/procurar_produto.html', context)
    else:
        return HttpResponseRedirect(reverse('loja:index'))



# --------------------- Carrinho ---------------------

def carrinho(request):
    lista_carrinho = request.session['lista_carrinho']
    lista_produtos = []
    total = 0
    for produto_id in lista_carrinho:
        produto = get_object_or_404(Produto, pk=int(produto_id))
        lista_produtos.append(produto)
        total += produto.preco_data * lista_carrinho[produto_id]
    context = {'lista_carrinho': lista_produtos, 'total': total, 'lista_carrinho_dict': lista_carrinho}
    return render(request, 'loja/carrinho.html', context)


def adicionar_produto(request,produto_id):
    lista_carrinho = request.session['lista_carrinho']
    lista_carrinho[str(produto_id)] += 1
    request.session['lista_carrinho'] = lista_carrinho
    return HttpResponseRedirect(reverse('loja:carrinho'))


def remover_produto(request, produto_id):
    lista_carrinho = request.session['lista_carrinho']
    if lista_carrinho[str(produto_id)] >= 2:
        lista_carrinho[str(produto_id)] -= 1
    request.session['lista_carrinho'] = lista_carrinho
    return HttpResponseRedirect(reverse('loja:carrinho'))


def adicionar_carrinho(request, produto_id):
    if not 'lista_carrinho' in request.session or not request.session['lista_carrinho']:
        dictionary = dict([(produto_id,1)])
        request.session['lista_carrinho'] = dictionary
    else:
        lista_carrinho = request.session['lista_carrinho']
        if not str(produto_id) in lista_carrinho:
            lista_carrinho[produto_id] = 1
            request.session['lista_carrinho'] = lista_carrinho
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def comprar(request, value='total'):
    lista_carrinho = request.session['lista_carrinho']
    compra = Compras.objects.create(cliente=request.user.cliente, total=float(value), date=datetime.datetime.now())
    for produto_id in lista_carrinho:
        produto = get_object_or_404(Produto, pk=int(produto_id))
        compra.produtos.add(produto)
    compra.save()
    request.session['lista_carrinho'] = {}
    return HttpResponseRedirect(reverse('loja:index'))


def buy_history(request):
    if request.user.is_superuser:
        lista_compras = Compras.objects.all()
    else:
        lista_compras = []
        for compra in Compras.objects.all():
            if compra.cliente == request.user.cliente:
                lista_compras.append(compra)
    return render(request, 'loja/buy_history.html', {'lista_compras':lista_compras})


def remover_carrinho(request, produto_id):
    lista_carrinho = request.session['lista_carrinho']
    lista_carrinho.pop(str(produto_id),None)
    request.session['lista_carrinho'] = lista_carrinho
    return HttpResponseRedirect(reverse('loja:carrinho'))

