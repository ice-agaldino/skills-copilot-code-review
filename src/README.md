# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades
- Login de professores para operacoes administrativas
- Anuncios dinamicos carregados do banco de dados
- Gerenciamento de anuncios (criar, editar, excluir) para usuarios autenticados

## Como começar

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| POST   | `/auth/login?username={username}&password={password}`            | Realiza login de professor                                            |
| GET    | `/auth/check-session?username={username}`                        | Valida sessao por usuario                                             |
| GET    | `/announcements/active`                                           | Lista anuncios ativos (publico)                                       |
| GET    | `/announcements?teacher_username={username}`                      | Lista todos os anuncios para gerenciamento (autenticado)              |
| POST   | `/announcements?teacher_username={username}`                      | Cria anuncio com expiracao obrigatoria e inicio opcional              |
| PUT    | `/announcements/{announcement_id}?teacher_username={username}`    | Atualiza anuncio existente                                             |
| DELETE | `/announcements/{announcement_id}?teacher_username={username}`    | Exclui anuncio                                                         |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Os dados sao armazenados no MongoDB local configurado no backend.
