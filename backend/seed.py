#!/usr/bin/env python3
"""
Popula o banco com livros reais e anotações em português.

Execute dentro do Docker:
  docker compose exec backend python seed.py

Depois, chame POST /api/annotations/embed-all para gerar embeddings.
Os embeddings são gerados localmente (fastembed) — nenhuma API key adicional necessária.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal, Base, engine
from app.models.annotation import Annotation
from app.models.book import Book
from sqlalchemy import text

BOOKS = [
    {
        "title": "Trabalho Focado: Como Ter Sucesso em um Mundo Distraído",
        "author": "Cal Newport",
        "genre": "Produtividade",
        "isbn": "978-1455586691",
        "year_published": 2016,
        "rating": 5.0,
        "status": "read",
        "description": "Cal Newport argumenta que a capacidade de foco profundo está se tornando rara e valiosa ao mesmo tempo. Um guia para cultivar a habilidade de trabalhar sem distrações em um mundo que conspira contra a concentração.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781455586691-M.jpg",
        "annotations": [
            {
                "type": "highlight",
                "content": "Trabalho focado é a capacidade de se concentrar sem distrações em uma tarefa cognitivamente exigente. É uma habilidade que permite dominar informações complexas rapidamente e produzir melhores resultados em menos tempo.",
                "chapter": "Introdução",
            },
            {
                "type": "highlight",
                "content": "A capacidade de realizar trabalho focado está se tornando cada vez mais rara exatamente ao mesmo tempo em que está se tornando cada vez mais valiosa em nossa economia. Como consequência, os poucos que cultivam essa habilidade e a colocam no centro de sua vida profissional prosperarão.",
                "chapter": "Capítulo 1: O Trabalho Focado é Valioso",
            },
            {
                "type": "note",
                "content": "Newport distingue dois tipos de trabalho: Trabalho Focado (concentrado, cognitivamente exigente, cria novo valor) e Trabalho Superficial (logístico, fácil de replicar, pouco valor). O insight principal é que a maioria dos trabalhadores do conhecimento passa tempo demais em trabalho superficial — email, reuniões, redes sociais — e pouco em trabalho profundo.",
                "chapter": "Capítulo 1",
            },
            {
                "type": "quote",
                "content": "Clareza sobre o que importa fornece clareza sobre o que não importa.",
                "chapter": "Capítulo 2: O Trabalho Focado é Raro",
            },
            {
                "type": "quote",
                "content": "Se você não produz, não prosperará — independentemente de quão habilidoso ou talentoso seja.",
                "chapter": "Capítulo 1",
            },
            {
                "type": "reflection",
                "content": "Preciso bloquear 2-3 horas de trabalho profundo ininterrupto toda manhã antes de checar email ou Slack. Sem telefone, sem notificações. É quando faço meu melhor trabalho criativo e analítico. Tratar esse bloco como uma reunião importante e intransferível.",
            },
        ],
    },
    {
        "title": "Hábitos Atômicos: Um Método Fácil e Comprovado para Criar Bons Hábitos e Eliminar os Maus",
        "author": "James Clear",
        "genre": "Produtividade",
        "isbn": "978-0735211292",
        "year_published": 2018,
        "rating": 5.0,
        "status": "read",
        "description": "James Clear revela estratégias práticas para formar bons hábitos, quebrar os ruins e dominar os pequenos comportamentos que levam a resultados notáveis. A obra mais completa sobre a ciência dos hábitos.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780735211292-M.jpg",
        "annotations": [
            {
                "type": "quote",
                "content": "Você não sobe ao nível dos seus objetivos. Você desce ao nível dos seus sistemas.",
                "chapter": "Introdução",
            },
            {
                "type": "highlight",
                "content": "Hábitos são os juros compostos do autoaperfeiçoamento. Da mesma forma que o dinheiro se multiplica por meio dos juros compostos, os efeitos dos seus hábitos se multiplicam à medida que você os repete.",
                "chapter": "Capítulo 1: O Poder Surpreendente dos Hábitos Atômicos",
            },
            {
                "type": "note",
                "content": "As Quatro Leis da Mudança de Comportamento: 1) Torne óbvio (Gatilho), 2) Torne atraente (Desejo), 3) Torne fácil (Resposta), 4) Torne satisfatório (Recompensa). Para quebrar um hábito ruim, inverta: torne invisível, não atraente, difícil e insatisfatório.",
                "chapter": "Parte II",
            },
            {
                "type": "quote",
                "content": "Cada ação que você realiza é um voto pelo tipo de pessoa que deseja se tornar.",
                "chapter": "Capítulo 2: Como Seus Hábitos Moldam Sua Identidade",
            },
            {
                "type": "highlight",
                "content": "A forma mais eficaz de motivação é o progresso. Quando recebemos um sinal de que estamos avançando, nos sentimos mais motivados a continuar nesse caminho.",
                "chapter": "Capítulo 15",
            },
            {
                "type": "reflection",
                "content": "O conceito de hábitos baseados em identidade mudou minha forma de pensar sobre mudança. Em vez de 'o que quero alcançar?', devo perguntar 'quem quero me tornar?'. Uma leitora lê todo dia. Uma pessoa saudável se exercita. É sobre identidade, não resultados. A cada pequena ação, estou votando pela pessoa que quero ser.",
            },
        ],
    },
    {
        "title": "Silêncio: O Poder dos Introvertidos em um Mundo que Não Para de Falar",
        "author": "Susan Cain",
        "genre": "Psicologia",
        "isbn": "978-0307352149",
        "year_published": 2012,
        "rating": 5.0,
        "status": "read",
        "description": "Susan Cain argumenta que subestimamos dramaticamente os introvertidos. Um mapa para entender introversão como força, não como falha — e para criar espaços onde introvertidos possam prosperar.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780307352149-M.jpg",
        "annotations": [
            {
                "type": "highlight",
                "content": "Introversão não é uma falha a ser corrigida. É um traço de personalidade com pontos fortes enormes: preferência por ambientes menos estimulantes, tendência ao pensamento cuidadoso e à introspecção, e a capacidade de se concentrar profundamente.",
                "chapter": "Introdução",
            },
            {
                "type": "quote",
                "content": "O segredo da vida é se colocar na iluminação certa. Para alguns, é um holofote de Broadway; para outros, uma mesa com uma lâmpada acesa.",
                "chapter": "Capítulo 1",
            },
            {
                "type": "note",
                "content": "Cain faz uma distinção crucial: introversão vs timidez. Introversão é sobre preferência de estimulação (introvertidos preferem menos). Timidez é sobre medo de julgamento social. Você pode ser um extrovertido tímido ou um introvertido confiante. São coisas completamente diferentes e confundi-las prejudica introvertidos que não são tímidos.",
                "chapter": "Introdução",
            },
            {
                "type": "quote",
                "content": "Não pense na introversão como algo que precisa ser curado. Passe seu tempo livre da forma que preferir, não da forma que acha que deveria.",
                "chapter": "Capítulo 10",
            },
            {
                "type": "highlight",
                "content": "Muitas das pessoas mais imaginativas e empáticas do mundo são introvertidas. Sem introvertidos, não teríamos o iPhone, o Google, Harry Potter e a teoria da relatividade.",
                "chapter": "Capítulo 2",
            },
            {
                "type": "reflection",
                "content": "Esse livro me ajudou a entender que minha necessidade de tempo sozinha após eventos sociais não é antissocial — é como me recarrego. Não sou quebrada. Processo o mundo de forma diferente. Devo parar de me desculpar por precisar de tempo para pensar antes de falar ou por preferir conversas profundas a small talk.",
            },
        ],
    },
    {
        "title": "As 5 Linguagens do Amor: O Segredo do Amor Duradouro",
        "author": "Gary Chapman",
        "genre": "Relacionamentos",
        "isbn": "978-0802473158",
        "year_published": 1992,
        "rating": 4.0,
        "status": "read",
        "description": "Gary Chapman identifica cinco linguagens do amor e guia casais para uma compreensão mais profunda de como cada pessoa dá e recebe amor. Um dos livros de relacionamentos mais vendidos de todos os tempos.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780802473158-M.jpg",
        "annotations": [
            {
                "type": "highlight",
                "content": "As cinco linguagens do amor são: Palavras de Afirmação, Atos de Serviço, Receber Presentes, Tempo de Qualidade e Toque Físico. Cada pessoa tem uma linguagem do amor primária que fala mais profundamente a ela do que todas as outras.",
                "chapter": "Capítulo 1",
            },
            {
                "type": "note",
                "content": "O insight principal: tendemos a dar amor na linguagem QUE QUEREMOS RECEBER, não na linguagem que nosso parceiro precisa. Isso cria uma desconexão dolorosa onde ambos amam muito, mas nenhum se sente amado. A solução é aprender a linguagem do amor do outro e falar ela, mesmo que não venha naturalmente.",
                "chapter": "Capítulo 2",
            },
            {
                "type": "quote",
                "content": "Precisamos estar dispostos a aprender a linguagem do amor primária do nosso cônjuge se quisermos ser comunicadores eficazes de amor.",
                "chapter": "Capítulo 3",
            },
            {
                "type": "reflection",
                "content": "Minha linguagem principal do amor é Tempo de Qualidade — me sinto mais amada quando alguém me dá atenção total e exclusiva, sem celular ou distrações. Minha secundária é Palavras de Afirmação. Entender isso me ajuda a comunicar o que preciso nos relacionamentos ao invés de me sentir magoada sem saber o porquê.",
            },
        ],
    },
    {
        "title": "Rápido e Devagar: Duas Formas de Pensar",
        "author": "Daniel Kahneman",
        "genre": "Psicologia",
        "isbn": "978-0374533557",
        "year_published": 2011,
        "rating": 5.0,
        "status": "read",
        "description": "Daniel Kahneman, Prêmio Nobel de Economia, explora os dois sistemas que dirigem a forma como pensamos: o Sistema 1 — rápido, intuitivo e emocional; e o Sistema 2 — lento, deliberativo e lógico.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780374533557-M.jpg",
        "annotations": [
            {
                "type": "highlight",
                "content": "O Sistema 1 opera automática e rapidamente, com pouco ou nenhum esforço e sem qualquer senso de controle voluntário. O Sistema 2 aloca atenção às atividades mentais esforçadas que o exigem, incluindo cálculos complexos.",
                "chapter": "Introdução",
            },
            {
                "type": "note",
                "content": "O princípio WYSIATI (O que você vê é tudo que existe): o Sistema 1 constrói a melhor história possível com as informações disponíveis, sem se perguntar sobre informações ausentes. Por isso primeiras impressões são tão poderosas — e tão perigosas. Julgamos com base no que está na frente dos nossos olhos.",
                "chapter": "Capítulo 7",
            },
            {
                "type": "quote",
                "content": "Nada na vida é tão importante quanto você pensa que é, enquanto está pensando nisso.",
                "chapter": "Capítulo 38: Pensando sobre a Vida",
            },
            {
                "type": "reflection",
                "content": "O viés de ancoragem está em todo lugar. Sempre que negocio preço ou estimo prazo, o primeiro número mencionado molda todo o raciocínio subsequente. Agora me pergunto deliberadamente: de qual âncora estou partindo, e ela é arbitrária? Isso mudou como faço negociações.",
            },
        ],
    },
    {
        "title": "Em Busca de Sentido",
        "author": "Viktor E. Frankl",
        "genre": "Filosofia",
        "isbn": "978-0807014271",
        "year_published": 1946,
        "rating": 5.0,
        "status": "read",
        "description": "Viktor Frankl narra suas experiências como prisioneiro em campos de concentração nazistas e desenvolve a logoterapia: a busca por significado como força motivadora primária do ser humano. Um dos livros mais importantes do século XX.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780807014271-M.jpg",
        "annotations": [
            {
                "type": "quote",
                "content": "Tudo pode ser tirado de um homem, exceto uma coisa: a última das liberdades humanas — escolher a própria atitude diante de qualquer conjunto de circunstâncias, escolher o próprio caminho.",
                "chapter": "Parte Um: Experiências em um Campo de Concentração",
            },
            {
                "type": "quote",
                "content": "Quando não podemos mais mudar uma situação, somos desafiados a mudar a nós mesmos.",
                "chapter": "Parte Um",
            },
            {
                "type": "quote",
                "content": "Aqueles que têm um 'porquê' para viver podem suportar quase qualquer 'como'.",
                "chapter": "Parte Um",
            },
            {
                "type": "highlight",
                "content": "Logoterapia: a força motivacional primária de um ser humano é a busca por significado na vida. Diferente do prazer (Freud) ou do poder (Adler), Frankl argumenta que é o significado que nos sustenta através do sofrimento.",
                "chapter": "Parte Dois: Logoterapia em Poucas Palavras",
            },
            {
                "type": "reflection",
                "content": "O conceito de otimismo trágico de Frankl me marcou profundamente: otimismo diante da tragédia. Não positividade ingênua, mas a crença de que o sofrimento pode ter significado e que é possível encontrar razões para viver mesmo no pior dos cenários. Coragem não é ausência de medo, mas escolher agir apesar dele.",
            },
        ],
    },
    {
        "title": "A Coragem de Ser Imperfeito",
        "author": "Brené Brown",
        "genre": "Relacionamentos",
        "isbn": "978-1592408412",
        "year_published": 2012,
        "rating": 4.5,
        "status": "read",
        "description": "Com base em 12 anos de pesquisa, Brené Brown explora por que temos medo de mostrar quem somos de verdade — e como a vulnerabilidade é a origem da coragem, da criatividade e da conexão.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781592408412-M.jpg",
        "annotations": [
            {
                "type": "highlight",
                "content": "Vulnerabilidade não é fraqueza. E esse mito é profundamente perigoso. Vulnerabilidade é o berço da inovação, da criatividade e da mudança.",
                "chapter": "Capítulo 1",
            },
            {
                "type": "quote",
                "content": "A coragem começa com aparecer e deixar a gente mesma ser vista.",
                "chapter": "Introdução",
            },
            {
                "type": "note",
                "content": "A teoria da resiliência à vergonha: a vergonha cresce no sigilo, no silêncio e no julgamento. O antídoto é empatia. Quando falamos da vergonha, ela perde poder. A chave é distinguir vergonha ('Eu sou ruim') de culpa ('Fiz algo ruim'). Culpa motiva mudança; vergonha motiva esconder e isolar.",
                "chapter": "Capítulo 3",
            },
            {
                "type": "highlight",
                "content": "Perfeccionismo não é o mesmo que buscar o melhor de si. É a crença de que se vivermos perfeito, parecermos perfeitos e agirmos perfeito, podemos minimizar ou evitar a dor da culpa, do julgamento e da vergonha.",
                "chapter": "Capítulo 4",
            },
            {
                "type": "reflection",
                "content": "A pesquisa de Brown mostra que as pessoas com maior senso de pertencimento e amor são aquelas que acreditam ser dignas de amor e pertencimento — antes de terem 'merecido'. Dignidade não é algo que você conquista; é algo que você decide. Isso é radical e vai contra tudo que aprendi sobre precisar ganhar aprovação.",
            },
        ],
    },
    {
        "title": "Mentalidade: A Nova Psicologia do Sucesso",
        "author": "Carol S. Dweck",
        "genre": "Psicologia",
        "isbn": "978-0345472328",
        "year_published": 2006,
        "rating": 4.5,
        "status": "read",
        "description": "Carol Dweck, psicóloga de Stanford, revela o poder do mindset: como a crença simples sobre nossos talentos e habilidades — se são fixos ou podem crescer — determina em grande parte nosso sucesso e felicidade.",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780345472328-M.jpg",
        "annotations": [
            {
                "type": "highlight",
                "content": "Com uma mentalidade fixa, as pessoas acreditam que suas qualidades básicas, como inteligência ou talento, são simplesmente traços fixos. Com uma mentalidade de crescimento, as pessoas acreditam que suas habilidades mais básicas podem ser desenvolvidas por meio de dedicação e trabalho duro.",
                "chapter": "Capítulo 1",
            },
            {
                "type": "quote",
                "content": "Tornar-se é melhor do que ser.",
                "chapter": "Capítulo 3",
            },
            {
                "type": "note",
                "content": "O insight mais importante: elogiar crianças por inteligência (mentalidade fixa) na verdade as PREJUDICA. Elas evitam desafios para proteger o rótulo de 'inteligente'. Elogiar esforço (mentalidade de crescimento) as torna mais resilientes. Aprendem que lutar faz parte do aprendizado, não é evidência de burrice.",
                "chapter": "Capítulo 3",
            },
            {
                "type": "reflection",
                "content": "Cresci sendo chamada de 'superdotada', o que criou uma mentalidade fixa. Eu tinha medo de parecer burra, então evitava desafios onde pudesse falhar. Ler esse livro me ajudou a reformular o fracasso como informação, não como veredicto. Agora tento perguntar: 'o que posso aprender com isso?' em vez de 'isso significa que não sou boa o suficiente?'",
            },
        ],
    },
]


async def seed():
    print("Criando tabelas...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    # Verificar se já tem dados
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        count = await db.execute(select(func.count()).select_from(Book))
        existing = count.scalar()
        if existing > 0:
            print(f"Banco já tem {existing} livros. Pulando seed.")
            print("Para re-sedar, primeiro limpe o banco: docker compose down -v && docker compose up -d")
            return

    print(f"Inserindo {len(BOOKS)} livros...")
    total_annotations = 0

    async with AsyncSessionLocal() as db:
        for book_data in BOOKS:
            annotations_data = book_data.pop("annotations", [])
            book = Book(**book_data)
            db.add(book)
            await db.flush()

            for ann_data in annotations_data:
                annotation = Annotation(book_id=book.id, **ann_data)
                db.add(annotation)
                total_annotations += 1

        await db.commit()

    print(f"\n✅ Seed concluído!")
    print(f"   {len(BOOKS)} livros inseridos")
    print(f"   {total_annotations} anotações inseridas (todas em português)")
    print(f"\n📌 Próximo passo obrigatório para o chat funcionar:")
    print(f"   curl -X POST http://localhost:8000/api/annotations/embed-all")
    print(f"   (aguarde ~30 segundos para os embeddings serem gerados em background)")


if __name__ == "__main__":
    asyncio.run(seed())
