#!/usr/bin/env bash
# Read-only FlexNet report. Keep vendor output intact: formats vary by release.
set -u
set -o pipefail
export LC_ALL=C

usage() {
    cat <<'EOF'
Usage: bash LicenseUsage.sh [options]

Show Cadence and Synopsys feature usage and checkout owners, hosts and times.
Run on a machine with vendor-provided lmutil and access to the license servers.

  --vendor all|cadence|synopsys  Vendors to query (default: all configured vendors)
  --cadence-server SPEC         Default: CDS_LIC_FILE (e.g. 5280@license-host)
  --synopsys-server SPEC        Default: SNPSLMD_LICENSE_FILE
  --cadence-lmutil PATH         Default: CADENCE_LMUTIL, then LMUTIL, then lmutil
  --synopsys-lmutil PATH        Default: SYNOPSYS_LMUTIL, then LMUTIL, then lmutil
  --timeout SECONDS            Whole-query deadline per vendor (default: 30)
  --active-only                Hide feature blocks reporting zero checkouts
  -h, --help                   Show this help

SPEC may also be a license file or FlexNet server list; quote the entire value.
Reports use lmstat -S cdslmd / -S snpslmd to select the vendor's features.
Output is a human-readable snapshot, not the dashboard CSV or a usage history.
Exit: 0 = queries completed; 1 = a query failed; 2 = invalid/missing configuration.
EOF
}

die() { printf 'LicenseUsage: %s\n' "$*" >&2; exit 2; }

vendor=all
cadence_server=${CDS_LIC_FILE:-}
synopsys_server=${SNPSLMD_LICENSE_FILE:-}
cadence_lmutil=${CADENCE_LMUTIL:-${LMUTIL:-lmutil}}
synopsys_lmutil=${SYNOPSYS_LMUTIL:-${LMUTIL:-lmutil}}
query_timeout=30
active_only=false

while (( $# )); do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --active-only) active_only=true; shift ;;
        --vendor|--cadence-server|--synopsys-server|--cadence-lmutil|--synopsys-lmutil|--timeout)
            (( $# >= 2 )) && [[ -n $2 && $2 != --* ]] || die "Missing value for $1"
            case "$1" in
                --vendor) vendor=$2 ;;
                --cadence-server) cadence_server=$2 ;;
                --synopsys-server) synopsys_server=$2 ;;
                --cadence-lmutil) cadence_lmutil=$2 ;;
                --synopsys-lmutil) synopsys_lmutil=$2 ;;
                --timeout) query_timeout=$2 ;;
            esac
            shift 2 ;;
        *) die "Unknown option: $1 (use --help)" ;;
    esac
done

case "$vendor" in all|cadence|synopsys) ;; *) die "Invalid vendor: $vendor" ;; esac
[[ $query_timeout =~ ^[1-9][0-9]*$ ]] || die 'Timeout must be a positive integer'
command -v timeout >/dev/null 2>&1 || die 'GNU timeout is required'
if [[ $vendor == cadence && -z $cadence_server ]]; then
    die 'Set CDS_LIC_FILE or --cadence-server'
elif [[ $vendor == synopsys && -z $synopsys_server ]]; then
    die 'Set SNPSLMD_LICENSE_FILE or --synopsys-server'
elif [[ -z $cadence_server && -z $synopsys_server ]]; then
    die 'No servers configured; set CDS_LIC_FILE and/or SNPSLMD_LICENSE_FILE'
fi

query_vendor() {
    local label=$1 daemon=$2 server=$3 binary=$4 output result
    printf '\n=== %s license checkouts | %s | %s ===\n' \
        "$label" "$server" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    if ! command -v "$binary" >/dev/null 2>&1; then
        printf 'LicenseUsage: %s lmutil unavailable: %s\n' "$label" "$binary" >&2
        return 1
    fi
    # -t limits connection attempts; timeout also bounds a stalled query.
    output=$(timeout --kill-after=2s "${query_timeout}s" \
        "$binary" lmstat -c "$server" -S "$daemon" -t "$query_timeout" 2>&1)
    result=$?
    if $active_only; then
        printf '%s\n' "$output" | awk '
            BEGIN { show=1 }
            /^Users of / { show=($0 !~ /Total of 0 licenses? in use/) }
            show { print }
        '
    else
        printf '%s\n' "$output"
    fi
    if (( result != 0 )); then
        printf 'LicenseUsage: %s query failed (exit %s); usage is unknown.\n' \
            "$label" "$result" >&2
        return 1
    fi
    # Some lmutil releases print errors while returning success. This is a
    # best-effort check; retain the full output for diagnostics and new formats.
    if [[ -z $output ]] || printf '%s\n' "$output" | grep -Ei \
        'Error getting status|Cannot connect to license server|License server machine is down|Vendor daemon is down|No such feature exists|FLEX(net|lm) Licensing error|Users of .*[(]Error:|(^|[[:space:]])DOWN([[:space:]:]|$)' >/dev/null; then
        printf 'LicenseUsage: %s returned an empty/error report; usage is incomplete or unknown.\n' "$label" >&2
        return 1
    fi
}

status=0
if [[ $vendor == all || $vendor == cadence ]]; then
    if [[ -n $cadence_server ]]; then
        query_vendor Cadence cdslmd "$cadence_server" "$cadence_lmutil" || status=1
    else
        printf 'LicenseUsage: Cadence skipped (CDS_LIC_FILE not configured).\n' >&2
    fi
fi
if [[ $vendor == all || $vendor == synopsys ]]; then
    if [[ -n $synopsys_server ]]; then
        query_vendor Synopsys snpslmd "$synopsys_server" "$synopsys_lmutil" || status=1
    else
        printf 'LicenseUsage: Synopsys skipped (SNPSLMD_LICENSE_FILE not configured).\n' >&2
    fi
fi
exit "$status"
