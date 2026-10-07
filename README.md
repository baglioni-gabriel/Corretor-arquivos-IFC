# 🏗️ Validador Automático de Modelos IFC (IDS)

Este projeto consiste em um script Python (`Av_IFC.py`) desenvolvido para automatizar a auditoria e validação de modelos BIM no formato IFC. O sistema processa lotes de arquivos locais para extrair metadados estruturais e verificar a conformidade dos modelos contra um conjunto de regras preestabelecidas, gerando um relatório de conformidade em texto puro.

## 🚀 Funcionalidades

O script opera em duas frentes principais: extração de dados históricos e validação de regras geométricas/paramétricas.

### 1. Extração de Metadados
* **Autor (Header):** Identifica os autores no cabeçalho nativo do arquivo IFC[cite: 1].
* **Autor (Entidades):** Extrai nomes de instâncias `IfcPerson` e `IfcPersonAndOrganization`[cite: 1].
* **Histórico de Salvamentos:** Contabiliza os registros da entidade `IfcOwnerHistory` para mapear a rastreabilidade do arquivo[cite: 1].

### 2. Motor de Validação IDS
O modelo é submetido a uma checagem de 7 regras de qualidade e padronização (baseadas no padrão MCMV)[cite: 1]:
1. **Níveis:** Valida a existência de exatamente 2 pavimentos nomeados com o padrão `Level.*`[cite: 1].
2. **Cotas Geométricas:** Confere se a elevação do "Level 2" está contida no intervalo rigoroso entre 2.569m e 2.571m[cite: 1].
3. **Paredes:** Verifica a existência de exatamente 9 instâncias da parede `GENERIC_150mm` com material associado via `IfcRelAssociatesMaterial`[cite: 1].
4. **Portas:** Checa a tipologia e exige a presença de 5 portas do tipo `MADEIRA_LISA`[cite: 1].
5. **Lajes e Pisos:** Exige 8 lajes/pisos validados através da propriedade `Reference` no Property Set `Pset_SlabCommon`[cite: 1].
6. **Esquadrias:** Torna obrigatória a existência de exatamente 5 janelas (`IfcWindow`)[cite: 1].
7. **Cobertura:** Torna obrigatória a existência de exatamente 1 telhado (`IfcRoof`)[cite: 1].

## 🛠️ Tecnologias e Bibliotecas Utilizadas

* **Python 3**[cite: 1]
* **[IfcOpenShell](http://ifcopenshell.org/):** Biblioteca principal utilizada para manipulação, leitura e extração das propriedades do esquema IFC[cite: 1].
* **Regex (`re`):** Utilizado para validação flexível de nomenclaturas (ex: ignorando *case sensitive* ou caracteres de escape complexos)[cite: 1].
* **OS:** Para iteração e processamento em lote de diretórios[cite: 1].

## ⚙️ Como executar o projeto

1. Clone este repositório em sua máquina local.
2. Certifique-se de ter o Python instalado e instale a biblioteca IfcOpenShell:
   ```bash
   pip install ifcopenshell
