import os
import re
import ifcopenshell
import ifcopenshell.util.element

# ==========================================
# FUNÇÕES DE EXTRAÇÃO DE METADADOS
# ==========================================

def get_header_author(ifc):
    """Extrai o autor definido no cabeçalho do arquivo IFC."""
    try:
        authors = ifc.header.file_name.author
        if authors:
            return ", ".join(authors) if isinstance(authors, (list, tuple)) else str(authors)
    except Exception:
        pass
    return "Não informado"

def get_entity_author(ifc):
    """Extrai os nomes das entidades IfcPerson / IfcPersonAndOrganization."""
    try:
        persons = ifc.by_type("IfcPerson")
        names = []
        for p in persons:
            given = getattr(p, "GivenName", "") or ""
            family = getattr(p, "FamilyName", "") or ""
            full_name = f"{given} {family}".strip()
            if full_name:
                names.append(full_name)
        if names:
            return ", ".join(set(names))
    except Exception:
        pass
    return "Não informado"

def get_save_count(ifc):
    """Retorna a quantidade de registros no histórico de alterações (IfcOwnerHistory)."""
    try:
        histories = ifc.by_type("IfcOwnerHistory")
        return len(histories)
    except Exception:
        return 0

def has_material_association(element):
    """Verifica se o elemento possui associação de material."""
    for rel in getattr(element, "HasAssociations", []):
        if rel.is_a("IfcRelAssociatesMaterial"):
            return True
    return False

# ==========================================
# MOTOR DE VALIDAÇÃO DO IDS (7 REGRAS)
# ==========================================

def validate_ids_rules(ifc):
    """
    Aplica as 7 regras extraídas do arquivo ARQ_IDS_CHECKER.xml:
    1. Validação de Níveis (Exatamente 2 'Level.*')
    2. Cota do Level 2 (Elevação entre 2.569m e 2.571m)
    3. Paredes (Exatamente 9 paredes 'GENERIC_150mm' com material)
    4. Portas (Exatamente 5 portas 'MADEIRA_LISA')
    5. Pisos/Lajes (Exatamente 8 com Pset_SlabCommon.Reference)
    6. Janelas (Exatamente 5 janelas)
    7. Telhado (Exatamente 1 telhado)
    """
    passed_rules = 0
    total_rules = 7

    # Regra 1: Validação de Níveis
    storeys = ifc.by_type("IfcBuildingStorey")
    valid_storeys = [s for s in storeys if re.match(r"^Level.*", getattr(s, "Name", "") or "", re.IGNORECASE)]
    if len(valid_storeys) == 2:
        passed_rules += 1

    # Regra 2: Cota do Level 2
    level2 = [s for s in storeys if getattr(s, "Name", "") == "Level 2"]
    if len(level2) == 1:
        elev = getattr(level2[0], "Elevation", None)
        if elev is not None and (2.569 <= float(elev) <= 2.571):
            passed_rules += 1

    # Regra 3: Nomenclatura e Material de Paredes
    walls = ifc.by_type("IfcWall")
    wall_pattern = r".*(GENERIC_150mm|Genérica 150mm|Gen\\X\\E9rica 150mm).*"
    valid_walls = [
        w for w in walls 
        if re.match(wall_pattern, getattr(w, "Name", "") or "", re.IGNORECASE) and has_material_association(w)
    ]
    if len(valid_walls) == 9:
        passed_rules += 1

    # Regra 4: Tipologias de Portas
    doors = ifc.by_type("IfcDoor")
    door_pattern = r".*(MADEIRA_LISA|madeira lisa).*"
    valid_doors = [d for d in doors if re.match(door_pattern, getattr(d, "Name", "") or "", re.IGNORECASE)]
    if len(valid_doors) == 5:
        passed_rules += 1

    # Regra 5: Nomenclatura de Pisos e Lajes
    slabs = ifc.by_type("IfcSlab")
    slab_pattern = r".*(PISO_0,020m|Piso 0,020m|Laje 0,10m).*"
    valid_slabs = 0
    for s in slabs:
        psets = ifcopenshell.util.element.get_psets(s)
        ref_val = psets.get("Pset_SlabCommon", {}).get("Reference", "")
        if ref_val and re.match(slab_pattern, str(ref_val), re.IGNORECASE):
            valid_slabs += 1
    if valid_slabs == 8:
        passed_rules += 1

    # Regra 6: Obrigatoriedade de Janelas
    windows = ifc.by_type("IfcWindow")
    if len(windows) == 5:
        passed_rules += 1

    # Regra 7: Obrigatoriedade de Telhado
    roofs = ifc.by_type("IfcRoof")
    if len(roofs) == 1:
        passed_rules += 1

    conformity_percentage = (passed_rules / total_rules) * 100
    return round(conformity_percentage, 2)

# ==========================================
# PROCESSAMENTO EM LOTE E GERAÇÃO DO RELATÓRIO
# ==========================================

def process_ifc_folder(folder_path, output_txt_path):
    if not os.path.exists(folder_path):
        print(f"Erro: A pasta '{folder_path}' não foi encontrada.")
        return

    results = []
    
    # Processa todos os arquivos .ifc na pasta
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(".ifc"):
            file_path = os.path.join(folder_path, filename)
            try:
                ifc = ifcopenshell.open(file_path)
                
                auth_header = get_header_author(ifc)
                auth_entity = get_entity_author(ifc)
                saves = get_save_count(ifc)
                conformity = validate_ids_rules(ifc)
                
                results.append({
                    "arquivo": filename,
                    "autor_header": auth_header,
                    "autor_entidade": auth_entity,
                    "salvamentos": saves,
                    "conformidade": f"{conformity}%"
                })
            except Exception as e:
                print(f"Erro ao processar {filename}: {e}")

    # Formatação da tabela em texto puro (.txt)
    headers = ["Nome do Arquivo", "Autor (Header)", "Autor (Entidade)", "Nº Salvamentos", "% Conformidade IDS"]
    
    # Calcula a largura de cada coluna dinamicamente
    col_widths = {
        "arquivo": max(len(h) for h in [headers[0]] + [r["arquivo"] for r in results] or [15]),
        "autor_header": max(len(h) for h in [headers[1]] + [r["autor_header"] for r in results] or [15]),
        "autor_entidade": max(len(h) for h in [headers[2]] + [r["autor_entidade"] for r in results] or [15]),
        "salvamentos": max(len(h) for h in [headers[3]] + [str(r["salvamentos"]) for r in results] or [15]),
        "conformidade": max(len(h) for h in [headers[4]] + [r["conformidade"] for r in results] or [18]),
    }

    def format_row(val1, val2, val3, val4, val5):
        return (
            f"| {val1:<{col_widths['arquivo']}} "
            f"| {val2:<{col_widths['autor_header']}} "
            f"| {val3:<{col_widths['autor_entidade']}} "
            f"| {val4:^{col_widths['salvamentos']}} "
            f"| {val5:^{col_widths['conformidade']}} |"
        )

    separator = "+" + "+".join(["-" * (width + 2) for width in col_widths.values()]) + "+"

    lines = [
        "RELATÓRIO DE VALIDAÇÃO DE MODELOS IFC CONFORME IDS (PADRÃO MCMV)",
        "=" * len(separator),
        format_row(*headers),
        separator
    ]

    for r in results:
        lines.append(format_row(r["arquivo"], r["autor_header"], r["autor_entidade"], str(r["salvamentos"]), r["conformidade"]))

    lines.append(separator)

    # Grava o arquivo .txt
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Processamento concluído com sucesso! Relatório gerado em: {output_txt_path}")

# ==========================================
# EXECUÇÃO
# ==========================================
# Altere os caminhos para a sua estrutura local/Colab
PASTA_DOS_MODELOS = "C:/Users/gabri/OneDrive/Documentos/Poli/Monitoria - BIM/Arquivos para avaliação"
ARQUIVO_SAIDA_TXT = "C:/Users/gabri/OneDrive/Documentos/Poli/Monitoria - BIM/Arquivo resultado.txt"

# Executa o script
process_ifc_folder(PASTA_DOS_MODELOS, ARQUIVO_SAIDA_TXT)