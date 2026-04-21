"""Runner minimal de testes de hipótese para o case NovaShop.

Objetivo: este script contém apenas testes de hipótese e rotinas reproduzíveis
para investigar o pico de Novembro/2023 (Q4) e a alta taxa de cancelamento (Q5).

Uso:
  python scripts/analise.py --all
  python scripts/analise.py --q4-tests
  python scripts/analise.py --q5-tests

Notas:
- Exploração interativa e visualizações ficam nos notebooks (`questões/`).
- Este script é deliberadamente pequeno e focado para evitar "espaguete".
"""

from pathlib import Path
import argparse
import json
import logging
from typing import Dict, Any

import pandas as pd

try:
    from scipy.stats import norm
except Exception:
    norm = None

LOG = logging.getLogger("analise")


class DataLoader:
    """Carrega os CSVs limpos necessários para os testes."""

    FILES = {
        'pedidos': 'pedidos_limpo.csv',
        'clientes': 'clientes_limpo.csv',
        'tickets': 'tickets_suporte_limpo.csv',
        'itens': 'itens_pedido_limpo.csv',
        'produtos': 'produtos_limpo.csv',
        'avaliacoes': 'avaliacoes_limpo.csv'
    }

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def load(self, keys=None) -> Dict[str, pd.DataFrame]:
        keys = keys or list(self.FILES.keys())
        data: Dict[str, pd.DataFrame] = {}
        for k in keys:
            path = self.data_dir / self.FILES[k]
            if not path.exists():
                LOG.warning('Arquivo ausente: %s (esperado em %s)', k, path)
                data[k] = pd.DataFrame()
            else:
                data[k] = pd.read_csv(path, low_memory=False)

        # Parse datas quando presentes
        if 'pedidos' in data and 'data_pedido' in data['pedidos'].columns:
            data['pedidos']['data_pedido'] = pd.to_datetime(data['pedidos']['data_pedido'], errors='coerce')
        if 'tickets' in data:
            for c in ('data_abertura', 'data_resolucao'):
                if c in data['tickets'].columns:
                    data['tickets'][c] = pd.to_datetime(data['tickets'][c], errors='coerce')
        if 'avaliacoes' in data and 'data_avaliacao' in data['avaliacoes'].columns:
            data['avaliacoes']['data_avaliacao'] = pd.to_datetime(data['avaliacoes']['data_avaliacao'], errors='coerce')
        if 'clientes' in data and 'data_cadastro' in data['clientes'].columns:
            data['clientes']['data_cadastro'] = pd.to_datetime(data['clientes']['data_cadastro'], errors='coerce')

        return data


class HypothesisTester:
    """Executa e salva testes de hipótese focados (Q4 e Q5)."""

    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _to_csv(self, df: pd.DataFrame, name: str) -> None:
        df.to_csv(self.out_dir / name, index=False)

    def _to_json(self, obj: Any, name: str) -> None:
        with open(self.out_dir / name, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    def _two_prop_ztest(self, x1: int, n1: int, x2: int, n2: int) -> Dict[str, Any] | None:
        """Teste normal aproximado para duas proporções.

        Retorna dict {'z': ..., 'pvalue': ...}. Se `norm` não estiver disponível, retorna z apenas.
        """
        try:
            if n1 == 0 or n2 == 0:
                return None
            p1 = x1 / n1
            p2 = x2 / n2
            p_pool = (x1 + x2) / (n1 + n2)
            se = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
            if se == 0:
                return None
            z = (p1 - p2) / se
            if norm is None:
                return {'z': float(z), 'pvalue': None}
            pval = 2 * (1 - float(norm.cdf(abs(z))))
            return {'z': float(z), 'pvalue': float(pval)}
        except Exception:
            LOG.exception('Erro no two_prop_ztest')
            return None

    def q4_hypotheses(self, pedidos: pd.DataFrame, clientes: pd.DataFrame) -> Dict[str, Any]:
        """Testes para as hipóteses relacionadas ao pico de Nov/2023.

        Saídas:
        - q4_hypotheses.json (resumo dos testes)
        - q4_coupon_penetration.csv
        - q4_segment_share.csv
        - q4_status_distribution_by_month.csv
        """
        df = pedidos.copy()
        if df.empty:
            LOG.warning('Tabela `pedidos` vazia — Q4 não executado')
            return {'q4_hypotheses': None}

        df['ano_mes'] = df['data_pedido'].dt.strftime('%Y-%m')
        months = ['2023-11', '2024-11']
        out: Dict[str, Any] = {'coupon_penetration': {}, 'segment_share': {}, 'status_dist': {}, 'duplication': {}}

        # Coupon penetration
        for m in months:
            sub = df[df['ano_mes'] == m]
            total = int(len(sub))
            cupom = int((sub['cupom_desconto'].notnull() & (sub['cupom_desconto'].astype(str).str.strip() != '')).sum()) if total > 0 else 0
            pct = round(cupom / total * 100, 1) if total > 0 else None
            out['coupon_penetration'][m] = {'total': total, 'cupom_count': cupom, 'pct': pct}
        cup_table = pd.DataFrame.from_dict(out['coupon_penetration'], orient='index').reset_index().rename(columns={'index': 'ano_mes'})
        self._to_csv(cup_table, 'q4_coupon_penetration.csv')

        # Segment share (requires clientes)
        cli = clientes.rename(columns={'id': 'cliente_id'}) if not clientes.empty else pd.DataFrame()
        merged = df.merge(cli[['cliente_id', 'segmento']] if not cli.empty else pd.DataFrame(), on='cliente_id', how='left')
        for m in months:
            sub = merged[merged['ano_mes'] == m]
            if 'segmento' in sub.columns:
                seg = (sub['segmento'].fillna('UNKNOWN').astype(str).str.strip().str.upper()).value_counts(normalize=True).mul(100).round(1).to_dict()
            else:
                seg = {'UNKNOWN': 100.0}
            out['segment_share'][m] = seg
        seg_df = pd.DataFrame(out['segment_share']).T.fillna(0).reset_index().rename(columns={'index': 'ano_mes'})
        self._to_csv(seg_df, 'q4_segment_share.csv')

        # Status distribution per month
        for m in months:
            sub = df[df['ano_mes'] == m]
            st = sub['status'].value_counts(normalize=True).mul(100).round(1).to_dict()
            out['status_dist'][m] = st
        status_df = pd.DataFrame(out['status_dist']).T.fillna(0).reset_index().rename(columns={'index': 'ano_mes'})
        self._to_csv(status_df, 'q4_status_distribution_by_month.csv')

        # Duplication check for Nov/2023
        nov23 = df[df['ano_mes'] == '2023-11']
        n_dup = int(nov23.duplicated(subset=['id']).sum()) if not nov23.empty else 0
        out['duplication']['2023-11_total'] = int(len(nov23))
        out['duplication']['2023-11_duplicates'] = n_dup

        self._to_json(out, 'q4_hypotheses.json')
        return {'q4_hypotheses': out}

    def q5_tests(self, pedidos: pd.DataFrame, clientes: pd.DataFrame, tickets: pd.DataFrame | None = None) -> Dict[str, Any]:
        """Testes adicionais para investigar a alta taxa de cancelamento (Q5).

        Saídas:
        - q5_channel_cancel_rates_full.csv
        - q5_channel_tests.json
        """
        df = pedidos.copy()
        if df.empty:
            LOG.warning('Tabela `pedidos` vazia — Q5 não executado')
            return {'q5_tests': None}

        cli = clientes.rename(columns={'id': 'cliente_id'}) if not clientes.empty else pd.DataFrame()
        merged = df.merge(cli[['cliente_id', 'canal_aquisicao']] if not cli.empty else pd.DataFrame(), on='cliente_id', how='left')
        merged['is_cancelled'] = merged['status'].str.lower() == 'cancelado'

        out: Dict[str, Any] = {}

        if 'canal_aquisicao' in merged.columns:
            ca = merged.groupby('canal_aquisicao').agg(total_orders=('id', 'count'), cancelled=('is_cancelled', 'sum'), avg_value=('valor_total', 'mean')).reset_index()
            ca['cancel_rate'] = (ca['cancelled'] / ca['total_orders'] * 100).round(2)
            ca = ca.sort_values('cancel_rate', ascending=False).reset_index(drop=True)
            self._to_csv(ca, 'q5_channel_cancel_rates_full.csv')
            out['channel_summary'] = ca.to_dict('records')

            # compare trafego_pago vs others
            try:
                tp = ca[ca['canal_aquisicao'] == 'trafego_pago']
                if not tp.empty:
                    x1 = int(tp['cancelled'].iloc[0])
                    n1 = int(tp['total_orders'].iloc[0])
                    comps = {}
                    for _, row in ca.iterrows():
                        ch = row['canal_aquisicao']
                        if ch == 'trafego_pago':
                            continue
                        x2 = int(row['cancelled'])
                        n2 = int(row['total_orders'])
                        comps[f'trafego_pago_vs_{ch}'] = self._two_prop_ztest(x1, n1, x2, n2)
                    out['trafego_pago_comparisons'] = comps
            except Exception:
                LOG.exception('Erro em comparações por canal')

        # cupom effect overall
        try:
            with_cup = merged[merged['cupom_desconto'].notnull() & (merged['cupom_desconto'].astype(str).str.strip() != '')]
            without_cup = merged[~(merged['cupom_desconto'].notnull() & (merged['cupom_desconto'].astype(str).str.strip() != ''))]
            x1 = int(with_cup['is_cancelled'].sum())
            n1 = int(len(with_cup))
            x2 = int(without_cup['is_cancelled'].sum())
            n2 = int(len(without_cup))
            out['cupom_effect_overall'] = {'with': {'x': x1, 'n': n1}, 'without': {'x': x2, 'n': n2}, 'test': self._two_prop_ztest(x1, n1, x2, n2)}
        except Exception:
            out['cupom_effect_overall'] = None

        # cupom effect in Nov/2023
        try:
            df2 = df.copy()
            df2['ano_mes'] = df2['data_pedido'].dt.strftime('%Y-%m')
            nov = df2[df2['ano_mes'] == '2023-11']
            with_cup = nov[nov['cupom_desconto'].notnull() & (nov['cupom_desconto'].astype(str).str.strip() != '')]
            without_cup = nov[~(nov['cupom_desconto'].notnull() & (nov['cupom_desconto'].astype(str).str.strip() != ''))]
            x1 = int(with_cup['status'].str.lower().eq('cancelado').sum())
            n1 = int(len(with_cup))
            x2 = int(without_cup['status'].str.lower().eq('cancelado').sum())
            n2 = int(len(without_cup))
            out['cupom_effect_nov2023'] = {'with': {'x': x1, 'n': n1}, 'without': {'x': x2, 'n': n2}, 'test': self._two_prop_ztest(x1, n1, x2, n2)}
        except Exception:
            out['cupom_effect_nov2023'] = None

        self._to_json(out, 'q5_channel_tests.json')
        return {'q5_tests': out}


def main():
    parser = argparse.ArgumentParser(description='Hipóteses NovaShop (focado)')
    parser.add_argument('--data-dir', default='data', help='Pasta com os CSVs limpos')
    parser.add_argument('--out-dir', default='outputs', help='Pasta de saída')
    parser.add_argument('--all', action='store_true', help='Rodar todos os testes de hipótese')
    parser.add_argument('--q4-tests', action='store_true', help='Rodar testes/hipóteses para Q4 (Nov/2023)')
    parser.add_argument('--q5-tests', action='store_true', help='Rodar testes/hipóteses para Q5 (cancelamentos)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    loader = DataLoader(Path(args.data_dir))
    data = loader.load()
    tester = HypothesisTester(Path(args.out_dir))

    run_all = args.all or not any([args.q4_tests, args.q5_tests])
    summary: Dict[str, Any] = {}

    if run_all or args.q4_tests:
        LOG.info('Executando testes Q4 (hipóteses Nov/2023)')
        summary.update(tester.q4_hypotheses(data.get('pedidos', pd.DataFrame()), data.get('clientes', pd.DataFrame())))

    if run_all or args.q5_tests:
        LOG.info('Executando testes Q5 (cancelamentos)')
        summary.update(tester.q5_tests(data.get('pedidos', pd.DataFrame()), data.get('clientes', pd.DataFrame()), data.get('tickets')))

    # grava resumo compacto
    try:
        tester._to_json(summary, 'analysis_summary.json')
    except Exception:
        LOG.exception('Erro salvando resumo')

    LOG.info('Execução finalizada. Saídas em %s', Path(args.out_dir))


if __name__ == '__main__':
    main()
