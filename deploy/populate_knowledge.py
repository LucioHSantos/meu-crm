import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
django.setup()

from apps.ai_agent.models import AIAgent, KnowledgeBase, BusinessRule, KnowledgeDocument

agent, _ = AIAgent.objects.get_or_create(pk=1, defaults={'name': 'AI Assistant'})

agent.business_name = 'Instituto Veterinário Rio das Ostras (IVRO)'
agent.business_description = (
    'Instituição de ensino veterinário localizada em Rio das Ostras-RJ, '
    'oferecendo cursos livres, de extensão e pós-graduação na área veterinária. '
    'Endereço: Rua Washington Viana, 90 - Centro, Rio das Ostras-RJ, CEP 28893-012. '
    'WhatsApp: (22) 99883-4177. Site: https://ivro.com.br'
)
agent.system_prompt = (
    "Você é o assistente virtual do Instituto Veterinário Rio das Ostras (IVRO). "
    "Seu papel é ATENDER e VENDER cursos veterinários. Regras: "
    "1) Seja acolhedor, profissional e use linguagem clara e acessível. "
    "2) Conheça profundamente todos os cursos, valores, durações e diferenças entre curso livre, extensão e pós-graduação. "
    "3) QUALIFIQUE o lead: pergunte se é veterinário formado, estudante ou iniciante para recomendar o curso ideal. "
    "4) Apresente os benefícios de cada curso: certificação MEC, turmas reduzidas (18 vagas), prática real assistida. "
    "5) Ao falar de valores, mencione o parcelamento no cartão e o desconto no Pix. "
    "6) Se o cliente mostrar interesse, incentive a inscrição e peça contato via WhatsApp (22) 99883-4177. "
    "7) NUNCA invente informações. Se não souber algo, ofereça conectar com um atendente humano. "
    "8) Use as REGRAS DO NEGÓCIO e a BASE DE CONHECIMENTO para responder com precisão."
)
agent.save()
print('✅ Agent configured')

KnowledgeBase.objects.filter(agent=agent).delete()
BusinessRule.objects.filter(agent=agent).delete()

rules = [
    {
        'title': 'Política de Desconto',
        'content': (
            'Ofereça 10% de desconto para pagamento à vista via Pix. '
            'Para cursos de extensão (R$ 3.840), o valor à vista é R$ 3.500 (economia de ~R$ 340). '
            'Para pós-graduação (R$ 22.050), o valor à vista é R$ 19.800. '
            'Sempre destaque o parcelamento sem juros no cartão como alternativa.'
        ),
        'priority': 100,
    },
    {
        'title': 'Público-Alvo por Curso',
        'content': (
            'CURSOS LIVRES: Auxiliar Veterinário (200h, R$ 3.300), Auxiliar de Radiologia (100h, indisponível) e '
            'Nutrição para Cães (8h, R$ 290) — para iniciantes, estudantes e profissionais sem formação superior. '
            'CURSOS DE EXTENSÃO: Cardiologia, Nefrologia/Urologia, Endocrinologia (108h, R$ 3.840 cada), '
            'Castração (27h, R$ 1.200), Ultrassom Abdominal (108h) e Clínica de Felinos (108h, R$ 1.450) '
            '— para médicos veterinários formados e estudantes de veterinária. '
            'PÓS-GRADUAÇÃO (lato sensu): 360h, R$ 22.050 cada — para veterinários formados e residentes.'
        ),
        'priority': 90,
    },
    {
        'title': 'Tom de Voz e Abordagem',
        'content': (
            'Seja educado, entusiasta e prestativo. Use "você" ou "senhor(a)". '
            'Destaque os diferenciais do IVRO: certificação MEC, turmas de apenas 18 alunos, '
            'professores com vivência clínica, foco na prática, e formação em Rio das Ostras (Região dos Lagos). '
            'Use frases como "Nosso diferencial é o ensino prático com cirurgiões atuantes no mercado."'
        ),
        'priority': 80,
    },
    {
        'title': 'Objeção de Preço',
        'content': (
            'Se o cliente achar caro: 1) Destaque o parcelamento acessível (ex: 12x de R$ 275 para Auxiliar Veterinário). '
            '2) Reforce o valor do certificado com reconhecimento MEC e validade nacional. '
            '3) Mencione que são apenas 18 vagas — ensino personalizado. '
            '4) Ofereça o desconto no Pix como alternativa. '
            '5) Compare com o retorno profissional: "Em 2 meses de trabalho você recupera o investimento."'
        ),
        'priority': 70,
    },
    {
        'title': 'Encaminhamento para WhatsApp',
        'content': (
            'Quando o cliente demonstrar interesse real em se inscrever, peça para entrar em contato '
            'pelo WhatsApp (22) 99883-4177 ou diga que pode anotar os dados para um retorno. '
            'Nunca force a venda. Se o cliente pedir 2 vezes para falar com um humano, transfira imediatamente.'
        ),
        'priority': 60,
    },
    {
        'title': 'Horário de Funcionamento',
        'content': (
            'O Instituto funciona em horário comercial, de segunda a sexta. '
            'Para informações sobre próximas turmas e datas, o cliente deve entrar em contato pelo WhatsApp.'
        ),
        'priority': 50,
    },
]

knowledge_items = [
    # INSTITUCIONAL
    {'category': 'faq', 'question': 'O que é o IVRO?', 'answer': 'IVRO é a sigla do Instituto Veterinário Rio das Ostras, uma instituição de ensino veterinário localizada em Rio das Ostras-RJ. Oferecemos cursos livres, de extensão e pós-graduação na área veterinária.'},
    {'category': 'contact', 'question': 'Onde fica o Instituto?', 'answer': 'Rua Washington Viana, 90 - Centro, Rio das Ostras - RJ, CEP 28893-012.'},
    {'category': 'contact', 'question': 'Qual o WhatsApp do Instituto?', 'answer': '(22) 99883-4177. O link direto é https://wa.me/5522998834177'},
    {'category': 'contact', 'question': 'Qual o site do Instituto?', 'answer': 'https://ivro.com.br'},
    {'category': 'faq', 'question': 'Quem é a coordenadora técnica?', 'answer': 'Dra. Mariana Mendonça, graduada em Medicina Veterinária há 10 anos, com pós-graduação em Nefrologia, Urologia, Endocrinologia e Diagnóstico por Imagem. É professora convidada da Universidade Salgado de Oliveira e professora do curso de Auxiliar Veterinário desde 2018.'},
    {'category': 'faq', 'question': 'Quais os diferenciais do IVRO?', 'answer': '1) Foco na prática clínica real, 2) Professores são veterinários e cirurgiões atuantes, 3) Certificado reconhecido pelo MEC com validade nacional, 4) Turmas reduzidas de apenas 18 alunos, 5) Conteúdo aplicável ao dia a dia, 6) Formação prática em Rio das Ostras (Região dos Lagos).'},
    {'category': 'faq', 'question': 'O certificado tem validade MEC?', 'answer': 'Sim! Todos os cursos oferecem certificado com reconhecimento do MEC (Ministério da Educação), com validade em todo território nacional.'},

    # CURSO LIVRE: AUXILIAR VETERINÁRIO
    {'category': 'products', 'question': 'O que é o curso de Auxiliar Veterinário?', 'answer': 'Curso livre de 200 horas com investimento de R$ 3.300 (12x de R$ 275) ou R$ 2.970 à vista no Pix. Ideal para iniciantes que querem trabalhar em clínicas, hospitais e pet shops. Aborda: contenção segura, biossegurança, preparo de materiais, apoio em consultas, noções de enfermagem veterinária, recepção e atendimento ao tutor. Certificado MEC.'},
    {'category': 'products', 'question': 'Qual a carga horária do Auxiliar Veterinário?', 'answer': '200 horas.'},
    {'category': 'products', 'question': 'Quanto custa o Auxiliar Veterinário?', 'answer': 'R$ 3.300 no cartão (12x de R$ 275) ou R$ 2.970 à vista no Pix (10% de desconto).'},
    {'category': 'products', 'question': 'Precisa de formação para fazer Auxiliar Veterinário?', 'answer': 'Não. Não exige conhecimento prévio. Apenas idade mínima de 16 anos e ensino fundamental completo.'},
    {'category': 'products', 'question': 'Onde o Auxiliar Veterinário pode trabalhar?', 'answer': 'Hospitais 24h, clínicas de pequenos animais, pet shops, farmácias veterinárias, principalmente na Região dos Lagos.'},

    # CURSO LIVRE: NUTRIÇÃO PARA CÃES
    {'category': 'products', 'question': 'O que é o curso de Nutrição para Cães?', 'answer': 'Curso livre de 8 horas com investimento de R$ 290 (3x de R$ 99) ou R$ 290 à vista no Pix. Aborda: pilares da nutrição canina, leitura de rótulos, alimentos proibidos, alimentação natural balanceada, prevenção de obesidade e diabetes, suplementação. Ideal para tutores, estudantes e criadores.'},

    # CURSO DE EXTENSÃO: CARDIOLOGIA
    {'category': 'services', 'question': 'O que é a Extensão em Cardiologia Veterinária?', 'answer': 'Curso de extensão de 108 horas para médicos veterinários e estudantes. Investimento: R$ 3.840 (12x de R$ 320) ou R$ 3.500 à vista. Aborda: semiologia cardiovascular, cardiopatias congênitas e adquiridas, interpretação de ECG e imagem, controle farmacológico de ICC, emergências cardiovasculares e estudo de casos clínicos reais.'},

    # CURSO DE EXTENSÃO: NEFROLOGIA
    {'category': 'services', 'question': 'O que é a Extensão em Nefrologia e Urologia Veterinária?', 'answer': 'Curso de extensão de 108 horas para médicos veterinários e estudantes. Investimento: R$ 3.840 (12x de R$ 320) ou R$ 3.500 à vista. Aborda: interpretação de urinálise e marcadores renais, DRA e DRC, diagnóstico por imagem renal e urológico, obstrução uretral e FLUTD, reposição eletrolítica e fluidoterapia, hipertensão arterial sistêmica de causa renal.'},

    # CURSO DE EXTENSÃO: ENDOCRINOLOGIA
    {'category': 'services', 'question': 'O que é a Extensão em Endocrinologia Veterinária?', 'answer': 'Curso de extensão de 108 horas para médicos veterinários e estudantes. Investimento: R$ 3.840 (12x de R$ 320) ou R$ 3.500 à vista. Aborda: Diabetes Mellitus, Hiperadrenocorticismo (Cushing), Hipo e Hipertireoidismo, interpretação de exames hormonais, e manejo de pacientes de difícil controle.'},

    # CURSO DE EXTENSÃO: CASTRACAO
    {'category': 'services', 'question': 'O que é a Extensão em Técnicas de Castração?', 'answer': 'Curso de extensão de 27 horas para veterinários e estudantes em final de curso. Investimento: R$ 1.200 (6x de R$ 200) ou R$ 1.200 à vista. Aborda: esterilização de materiais, anatomia cirúrgica, técnica OSH com gancho de Snook, ligaduras, nós e suturas hemostáticas, complicações intraoperatórias, protocolo anestésico e analgesia pós-operatória. Inclui demonstrações cirúrgicas reais.'},

    # CURSO DE EXTENSÃO: ULTASSOM
    {'category': 'services', 'question': 'O que é a Extensão em Ultrassom Abdominal?', 'answer': 'Curso de extensão de 108 horas para médicos veterinários e estudantes. Aborda: física do ultrassom, anatomia ecográfica sistemática, avaliação de fígado, vesícula e baço, trato urinário, diferenciação intestinal e detecção de corpos estranhos, e redação de laudos.'},

    # CURSO DE EXTENSÃO: CLÍNICA DE FELINOS
    {'category': 'services', 'question': 'O que é a Extensão em Clínica de Felinos?', 'answer': 'Curso de extensão de 108 horas para médicos veterinários e estudantes. Investimento: R$ 1.450 (10x de R$ 145) ou R$ 1.300 à vista. Aborda: design ambiental e atendimento cat-friendly, metabolismo farmacológico felino, cardiomiopatias, a tríade felina (DRC, hipertireoidismo, tríade), FIV e FeLV, emergências respiratórias. Professora: Dra. Thais Muniz Lopes, especialista em Medicina Felina.'},

    # PÓS-GRADUAÇÃO
    {'category': 'services', 'question': 'Quais pós-graduações o IVRO oferece?', 'answer': 'Pós-graduação lato sensu (360h, R$ 22.050 ou 21x R$ 1.050) em: Cardiologia Veterinária, Nefrologia e Urologia Veterinária, Endocrinologia Veterinária, Cirurgia de Tecidos Moles, Ultrassom Abdominal, e Clínica de Felinos. Para veterinários formados e residentes.'},

    # PAGAMENTO
    {'category': 'pricing', 'question': 'Quais formas de pagamento são aceitas?', 'answer': 'Cartão de crédito com parcelamento (até 12x dependendo do curso) e Pix com desconto. O pagamento é processado pela InfinitePay.'},
    {'category': 'pricing', 'question': 'Tem desconto para pagamento à vista?', 'answer': 'Sim! Pagamento no Pix tem 10% de desconto na maioria dos cursos.'},

    # VAGAS E TURMAS
    {'category': 'faq', 'question': 'Quantas vagas por turma?', 'answer': 'Apenas 18 vagas por turma para garantir atendimento individualizado e máxima proximidade com os professores.'},
    {'category': 'hours', 'question': 'Quando abrem as próximas turmas?', 'answer': 'As turmas de 2026 estão em fase de definição. Para saber as próximas datas, entre em contato pelo WhatsApp (22) 99883-4177.'},

    # PROFESSORES
    {'category': 'faq', 'question': 'Quem é a professora de Clínica de Felinos?', 'answer': 'Dra. Thais Muniz Lopes. Bacharel em Medicina Veterinária pela UFMG (2004), mestranda em Fisiologia pela UFRJ, pós-graduada em Clínica e Cirurgia de Pequenos Animais (UNIP 2009), pós-graduada em Medicina Felina (CESMAC 2019 e FATEC 2020). Atendimento exclusivo a felinos desde 2017. Certificada pelo Cat Handling Programme (EUA, 2020). Membro da Feline Veterinary Medical Association. Prescritora de cannabis medicinal desde 2019.'},

    # DIFERENCIAIS INSTITUCIONAIS
    {'category': 'faq', 'question': 'O IVRO é presencial ou online?', 'answer': 'Os cursos são presenciais, realizados em Rio das Ostras-RJ, com supervisão de experiência prática.'},
    {'category': 'faq', 'question': 'O IVRO é reconhecido pelo MEC?', 'answer': 'Sim! Todos os certificados têm chancela oficial com reconhecimento do MEC e validade nacional.'},
    {'category': 'faq', 'question': 'O que significa "Formação Prática em Rio das Ostras"?', 'answer': 'Significa que o aluno aprende na prática, com atendimento supervisionado e simulação de casos reais, alinhado à demanda clínica da Região dos Lagos.'},
    {'category': 'faq', 'question': 'Qual o lema do IVRO?', 'answer': '"Formação • Prática • Propósito".'},
]


for item in knowledge_items:
    KnowledgeBase.objects.create(agent=agent, category=item['category'], question=item['question'], answer=item['answer'])
print(f'✅ {len(knowledge_items)} knowledge items created')

for rule in rules:
    BusinessRule.objects.create(agent=agent, title=rule['title'], content=rule['content'], priority=rule['priority'])
print(f'✅ {len(rules)} business rules created')

print('\n🎯 Knowledge base populated successfully!')
print(f'   - {KnowledgeBase.objects.filter(agent=agent).count()} knowledge items')
print(f'   - {BusinessRule.objects.filter(agent=agent).count()} business rules')
