import json
import os
import sys

# Import minimum sample thresholds from existing script
# We add the directory to sys.path to easily import it if needed, or we can just read them.
try:
    from scripts.process_microdata import MIN_SAMPLE_OCUPACAO, MIN_SAMPLE_GRUPO
except ImportError:
    MIN_SAMPLE_OCUPACAO = 20
    MIN_SAMPLE_GRUPO = 15

def build_regional_panel(uf_codes_path, subgroups_uf_path, scores_path, output_path):
    with open(uf_codes_path, 'r', encoding='utf-8') as f:
        uf_codes = json.load(f)
        
    uf_to_region = {v['sigla']: v['regiao'] for v in uf_codes.values()}
    
    with open(subgroups_uf_path, 'r', encoding='utf-8') as f:
        subgroups_by_uf = json.load(f)
        
    with open(scores_path, 'r', encoding='utf-8') as f:
        scores = json.load(f)
        
    # Region -> Occupation Code -> List of UF dictionaries
    region_data = {}
    
    for uf_sigla, occ_list in subgroups_by_uf.items():
        region = uf_to_region.get(uf_sigla)
        if not region:
            continue
            
        if region not in region_data:
            region_data[region] = {}
            
        for occ in occ_list:
            code = occ['code']
            if code not in region_data[region]:
                region_data[region][code] = []
            region_data[region][code].append(occ)
            
    panel = []
    
    for region, occs in region_data.items():
        for code, uf_list in occs.items():
            # Check exposure
            score_info = scores.get(code)
            if not score_info:
                continue
            exposure = score_info.get('exposure')
            if exposure is None:
                continue
                
            tier = score_info.get('tier')
            
            # Aggregate sample size
            total_sample = sum(uf.get('sample_size', 0) for uf in uf_list)
            
            threshold = MIN_SAMPLE_OCUPACAO if len(code) >= 4 else MIN_SAMPLE_GRUPO
            if total_sample < threshold:
                continue
                
            total_jobs = sum(uf.get('total_workers', 0) for uf in uf_list)
            if total_jobs <= 0:
                continue
                
            # Weighted averages
            jobs_with_age = sum(uf.get('total_workers', 0) for uf in uf_list if uf.get('avg_age') is not None)
            jobs_with_study = sum(uf.get('total_workers', 0) for uf in uf_list if uf.get('avg_study_years') is not None)
            jobs_with_income = sum(uf.get('total_workers', 0) for uf in uf_list if uf.get('avg_income') is not None)
            
            sum_age = sum(uf.get('avg_age', 0) * uf.get('total_workers', 0) for uf in uf_list if uf.get('avg_age') is not None)
            sum_study = sum(uf.get('avg_study_years', 0) * uf.get('total_workers', 0) for uf in uf_list if uf.get('avg_study_years') is not None)
            sum_income = sum(uf.get('avg_income', 0) * uf.get('total_workers', 0) for uf in uf_list if uf.get('avg_income') is not None)
            
            avg_age = round(sum_age / jobs_with_age, 1) if jobs_with_age > 0 else None
            avg_study = round(sum_study / jobs_with_study, 1) if jobs_with_study > 0 else None
            avg_renda = round(sum_income / jobs_with_income, 2) if jobs_with_income > 0 else None
            
            # Informality
            inf_num = sum(uf.get('informal_weight_numerator', 0) for uf in uf_list)
            inf_den = sum(uf.get('informal_weight_sum', 0) for uf in uf_list)
            if inf_den > 0:
                informality = round((inf_num / inf_den) * 100, 1)
            else:
                # Fallback
                jobs_with_inf = sum(uf.get('total_workers', 0) for uf in uf_list if uf.get('informality_rate') is not None)
                sum_inf = sum(uf.get('informality_rate', 0) * uf.get('total_workers', 0) for uf in uf_list if uf.get('informality_rate') is not None)
                informality = round(sum_inf / jobs_with_inf, 1) if jobs_with_inf > 0 else None
                
            # Predominant sector (weighted mode)
            sector_counts = {}
            for uf in uf_list:
                sec = uf.get('predominant_sector')
                if sec:
                    sector_counts[sec] = sector_counts.get(sec, 0) + uf.get('total_workers', 0)
            
            predominant_sector = None
            if sector_counts:
                predominant_sector = max(sector_counts.items(), key=lambda x: x[1])[0]
                
            row = {
                "region": region,
                "occupation_code": code,
                "occupation_name": uf_list[0].get('name'),
                "jobs": round(total_jobs, 2),
                "sample_size": total_sample,
                "exposure": exposure,
                "tier": tier,
                "avg_anos_estudo": avg_study,
                "avg_idade": avg_age,
                "renda": avg_renda,
                "informality": informality
            }
            if predominant_sector is not None:
                row["predominant_sector"] = predominant_sector
                
            panel.append(row)
            
    output = {
        "metadata": {
            "decisions": [
                "Célula abaixo de MIN_SAMPLE_OCUPACAO/MIN_SAMPLE_GRUPO é excluída (mesmo limiar já usado no resto do pipeline, não um novo).",
                "Ocupações com exposure: null ficam de fora do regressando desde já (não viram zero)."
            ]
        },
        "data": panel
    }
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_regional_panel(
        os.path.join(base_dir, 'scripts', 'reference', 'uf_codes.json'),
        os.path.join(base_dir, 'data/output/cod_subgroups_by_uf.json'),
        os.path.join(base_dir, 'data/output/scores.json'),
        os.path.join(base_dir, 'data/output/regional_panel.json')
    )
    print("Created data/output/regional_panel.json")
