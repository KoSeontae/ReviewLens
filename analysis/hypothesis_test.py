"""XyZ 가설 검정: 적어도 X%의 방문자(Y)는 분석 결과가 구매에 도움된다고 응답할 것이다(Z).

데이터: feedback_final 시트의 purchase_help 열 (yes/no).
방법: Exact Binomial Test (단측, alternative='greater').
표본이 작을 가능성이 높아 정규근사(z검정)보다 정확한 p-value를 주는 Exact Binomial을 사용한다.

사용법:
    python -m analysis.hypothesis_test --yes 18 --total 100 --x 0.15
"""

import argparse

from scipy.stats import binomtest


def run(yes: int, total: int, x: float) -> None:
    if yes > total or total <= 0:
        raise ValueError("yes는 total을 넘을 수 없고 total은 0보다 커야 합니다.")

    result = binomtest(yes, total, x, alternative="greater")
    observed = yes / total

    print(f"표본 크기(n)      : {total}")
    print(f"'예' 응답 수(k)    : {yes}")
    print(f"관측 비율          : {observed:.1%}")
    print(f"가설 임계값(X)     : {x:.1%}")
    print(f"p-value            : {result.pvalue:.4f}")
    print(f"95% CI (하한 기준) : {result.proportion_ci(confidence_level=0.95).low:.1%} 이상")

    alpha = 0.05
    if result.pvalue < alpha:
        print(f"\n결론: p < {alpha} → 가설 채택(적어도 {x:.0%}는 Z를 한다고 통계적으로 지지됨)")
    else:
        print(f"\n결론: p >= {alpha} → 가설 기각(적어도 {x:.0%}라는 주장을 지지할 근거 부족)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="XyZ 가설 Exact Binomial Test")
    parser.add_argument("--yes", type=int, required=True, help="'예'(도움됨) 응답 수")
    parser.add_argument("--total", type=int, required=True, help="전체 응답 수")
    parser.add_argument("--x", type=float, default=0.5, help="가설 임계 비율 (기본 0.5 = 50%)")
    args = parser.parse_args()
    run(args.yes, args.total, args.x)
