# Run the nsa2_matrix group (sample x backend x refinement path) headlessly in olex2c.
#
#   run_headless_matrix.ps1 -Rundir D:\devel\rundir-test -Samples sucrose -Backends SALTED,OCC,pTB,ORCA -Paths spherical,har1 -Full
#
# The working directory of olex2c is the run directory, so the run directory is
# the Olex2 base dir (GuessBaseDir falls back to the current directory when
# OLEX2_DIR is unset): NoSpherA2.exe, basis_sets, occ/share, ptb.exe are taken
# from there, and the user's own Olex2 DataDir is not touched (a fresh base dir
# hashes to its own DataDir). olex2c reads its commands from a file, one per
# line; the only line here is the @py that execs run_pipeline.py.
param(
  [string]$Rundir = "D:\devel\rundir-py3",
  [string]$Olex2c = "D:\git\olex2\build\msvc-2026\olex2\x64\debug\exe\olex2c.exe",
  [string]$Samples = "sucrose",
  [string]$Backends = "",
  [string]$Paths = "spherical,har1",
  [switch]$Full,
  [string]$Ncpus = "",
  [string]$SaltedModel = "D:\git\NoSpherA2\tests\SALTED\Model",
  [string]$Out = "",
  [string]$Python = "C:\Users\florian\AppData\Local\Python\pythoncore-3.12-64"
)
$ErrorActionPreference = "Stop"
$pkg = Join-Path $Rundir "util\pyUtil\regression\olex2_pipeline_tests"
if (-not (Test-Path (Join-Path $pkg "run_pipeline.py"))) { throw "no pipeline package under $pkg" }
if (-not (Test-Path $Olex2c)) { throw "no olex2c at $Olex2c" }
if (-not $Out) { $Out = Join-Path $Rundir "olex2_matrix_tests.txt" }
$work = Join-Path $Rundir "olex2_matrix_run"
New-Item -ItemType Directory -Force $work | Out-Null

$bld = Join-Path $Rundir "cctbx\cctbx_build"
$env:PYTHONHOME = $Python
$env:LIBTBX_BUILD = $bld
$env:PYTHONPATH = "$bld\..\cctbx_sources;$bld\..\cctbx_sources\boost_adaptbx;$bld\lib;$Python\Lib\site-packages"
$env:OLEX2_TEST_GROUPS = "nsa2_matrix"
$env:OLEX2_TEST_SAMPLES = $Samples
$env:OLEX2_TEST_BACKENDS = $Backends
$env:OLEX2_TEST_PATHS = $Paths
$env:OLEX2_TEST_FULL = $(if ($Full) { "1" } else { "" })
$env:OLEX2_TEST_NCPUS = $Ncpus
$env:OLEX2_TEST_SALTED_MODEL = $SaltedModel
$env:OLEX2_TEST_OUT = $Out
Remove-Item Env:OLEX2_DIR -ErrorAction SilentlyContinue

$script = (Join-Path $pkg "run_pipeline.py")
$cmds = Join-Path $work "cmds.txt"
"@py `"exec(open(r'$script').read())`"" | Set-Content -Encoding ascii $cmds
$stdout = Join-Path $work "out.txt"
$stderr = Join-Path $work "err.txt"
if (Test-Path $Out) { Remove-Item $Out }

Write-Host ("matrix: samples={0} backends={1} paths={2} full={3} rundir={4}" -f $Samples, ($Backends, "all")[!$Backends], $Paths, [bool]$Full, $Rundir)
$t0 = Get-Date
$p = Start-Process -FilePath $Olex2c -ArgumentList @("script", $cmds) -WorkingDirectory $Rundir `
       -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$p.WaitForExit()
Write-Host ("olex2c exit {0} after {1:n0} s" -f $p.ExitCode, ((Get-Date) - $t0).TotalSeconds)
if (Test-Path $Out) { Get-Content $Out } else { Write-Host "no result file $Out"; Get-Content $stdout -Tail 40 }
