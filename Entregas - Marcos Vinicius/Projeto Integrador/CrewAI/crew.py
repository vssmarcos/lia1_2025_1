from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class LiaAnaliseFinanceira():
	"""LiaAnaliseFinanceira crew"""


	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@before_kickoff
	def obter_dados_google_sheet_como_json(self, inputs):
		import requests
		import pandas as pd
		import json
		import io

		try:
			# Faz a requisição HTTP para obter o conteúdo do CSV
			response = requests.get(inputs['url'])
			response.raise_for_status()  # Lança um erro para status HTTP ruins (4xx ou 5xx)

			# O conteúdo da resposta é o nosso arquivo CSV em texto
			csv_content = response.text
			print(csv_content)

			# Usamos o pandas para ler o texto do CSV diretamente da memória
			# O `io.StringIO` trata uma string como se fosse um arquivo
			dataframe = pd.read_csv(io.StringIO(csv_content))

			# Converte o DataFrame para um formato de dicionário (lista de objetos)
			# O orient='records' cria o formato JSON mais comum para APIs: [{}, {}, {}]
			dados_em_dict = dataframe.to_dict(orient='records')

			# Converte o dicionário para uma string JSON formatada
			# ensure_ascii=False garante que caracteres como 'ç' e 'ã' sejam mantidos
			json_output = json.dumps(dados_em_dict, indent=4, ensure_ascii=False)

			inputs['lista'].append(json_output)

			return inputs

		except requests.exceptions.RequestException as e:
			return json.dumps([{"erro": f"Falha ao acessar a URL: {e}"}], indent=4)
		except pd.errors.EmptyDataError:
			return json.dumps([{"erro": "A planilha parece estar vazia."}], indent=4)
		except Exception as e:
			return json.dumps([{"erro": f"Ocorreu um erro inesperado: {e}"}], indent=4)




	@agent
	def financial_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['financial_analyst'],
			verbose=True
		)

	@agent
	def cost_optimizer(self) -> Agent:
		return Agent(
			config=self.agents_config['cost_optimizer'],
			verbose=True
		)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def analyze_spending_task(self) -> Task:
		return Task(
			config=self.tasks_config['analyze_spending_task'],
			output_file = 'analise.md'
		)

	@task
	def recommend_saving_plan_task(self) -> Task:
		return Task(
			config=self.tasks_config['recommend_saving_plan_task'],
			output_file='recomendações.md'
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the LiaAnaliseFinanceira crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
