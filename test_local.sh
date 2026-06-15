#!/bin/bash
# ============================================
# StemComposer — Test Local CI Pipeline
# ============================================
# Simulează exact ce rulează GitHub Actions.
# Usage: ./test_local.sh
# Usage: ./test_local.sh --docker   (include și build Docker)

set -e

# Culori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PASSED=0
FAILED=0

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
}

print_pass() {
    echo -e "${GREEN}${BOLD}  ✅ $1${NC}"
    PASSED=$((PASSED + 1))
}

print_fail() {
    echo -e "${RED}${BOLD}  ❌ $1${NC}"
    FAILED=$((FAILED + 1))
}

# ── 0. Pregătire mediu virtual ──
print_header "🔧 Pregătire mediu virtual"

VENV_DIR=".venv_ci_test"

if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "  Folosim venv-ul existent..."
else
    echo "  Creăm venv nou..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install -q -r requirements-dev.txt
print_pass "Dependințe instalate"

# ── 1. Lint — Erori critice ──
print_header "🧹 Lint — Erori critice (flake8)"

if flake8 app/ core/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
    print_pass "Zero erori critice de sintaxă"
else
    print_fail "Erori critice găsite! Pipeline-ul ar fi oprit."
fi

# ── 2. Lint — Avertismente ──
print_header "🧹 Lint — Avertismente stil (informativ)"
flake8 app/ core/ --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
echo -e "${YELLOW}  ⚠️  Avertismentele de mai sus NU opresc pipeline-ul${NC}"

# ── 3. Migrații ──
print_header "🗄️  Verificare migrații Django"

if python manage.py migrate --run-syncdb > /dev/null 2>&1; then
    print_pass "Migrațiile se aplică corect"
else
    print_fail "Eroare la migrații"
fi

# ── 4. Teste Django ──
print_header "🧪 Teste Django"

export DJANGO_SECRET_KEY="test-secret-key-for-local-ci"
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,testserver"

if python manage.py test app -v2; then
    print_pass "Toate testele au trecut"
else
    print_fail "Unele teste au picat!"
fi

# ── 5. Coverage ──
print_header "📊 Coverage"

coverage run manage.py test app -v0 2>/dev/null
COVERAGE_PCT=$(coverage report | tail -1 | awk '{print $NF}' | tr -d '%')
coverage report

if [ "$COVERAGE_PCT" -ge 70 ] 2>/dev/null; then
    print_pass "Coverage: ${COVERAGE_PCT}% (minim cerut: 70%)"
else
    print_fail "Coverage: ${COVERAGE_PCT}% — sub minimul de 70%"
fi

# ── 6. Docker Build (opțional) ──
if [ "$1" = "--docker" ]; then
    print_header "🐳 Docker Build — Django"
    if docker build -t stemcomposer-django:test -f Dockerfile . > /dev/null 2>&1; then
        print_pass "Django Dockerfile compilează"
    else
        print_fail "Django Dockerfile NU compilează"
    fi

    print_header "🐳 Docker Build — Demucs AI"
    if docker build -t stemcomposer-demucs:test -f dockerfile . > /dev/null 2>&1; then
        print_pass "Demucs Dockerfile compilează"
    else
        print_fail "Demucs Dockerfile NU compilează"
    fi
else
    echo ""
    echo -e "${YELLOW}  💡 Rulează cu ${BOLD}--docker${NC}${YELLOW} pentru a testa și Docker build:${NC}"
    echo -e "${YELLOW}     ./test_local.sh --docker${NC}"
fi

# ── 7. Curățare ──
deactivate
rm -f .coverage coverage.xml
rm -f db.sqlite3

# ── Raport final ──
print_header "📋 RAPORT FINAL"
echo ""
echo -e "  ${GREEN}✅ Passed: ${PASSED}${NC}"
echo -e "  ${RED}❌ Failed: ${FAILED}${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  🎉 Totul e OK! Poți da push în siguranță.${NC}"
    echo ""
    echo -e "  ${BOLD}git add -A${NC}"
    echo -e "  ${BOLD}git commit -m \"feat: add CI/CD pipeline\"${NC}"
    echo -e "  ${BOLD}git push origin main${NC}"
else
    echo -e "${RED}${BOLD}  ⛔ Rezolvă erorile înainte de push!${NC}"
fi

echo ""
echo -e "${YELLOW}  💡 Pentru a șterge venv-ul de test: rm -rf ${VENV_DIR}${NC}"
echo ""
