param(
    [ValidateSet("zips", "bags", "all")]
    [string]$Mode = "zips",

    [int]$Retries = 3
)

$ErrorActionPreference = "Stop"

$root = "D:\TorWIC-SLAM\TorWIC SLAM Dataset"
$blockedIds = @(
    "1RSJCHnl6WFFPD0Wdb43MEsTgxueyfhwu"
)

$items = @(
    [pscustomobject]@{ Id = "1WahCGK7lUGYBvXwcb5M83UHeNwQZJ0-G"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\aisle_ccw_run_1.bag" },
    [pscustomobject]@{ Id = "1BuFglb0w7U--BCt9Kve3-M0tDiWRtp0N"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\aisle_ccw_run_2.bag" },
    [pscustomobject]@{ Id = "1RSJCHnl6WFFPD0Wdb43MEsTgxueyfhwu"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\aisle_cw_run_1.bag" },
    [pscustomobject]@{ Id = "1-wU3Ogexj6McrN9LUs2VwcDOhFkhJ4VL"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\aisle_cw_run_2.bag" },
    [pscustomobject]@{ Id = "1v2u6Lc1ho3PlHtMKbWIAo8wqRqAFWFbD"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\hallway_full_ccw_part_1.bag" },
    [pscustomobject]@{ Id = "1Zi43hI0x__zjqkWqgYjN-KWJHu7ptHFg"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\hallway_full_ccw_part_2.bag" },
    [pscustomobject]@{ Id = "169adLtoFNYS_drJdeNELTHbFVra3DSXM"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\hallway_full_cw_part_1.bag" },
    [pscustomobject]@{ Id = "1zziS1YmJpRuZjK796_g01uvQgbcfaQxT"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\hallway_full_cw_part_2.bag" },
    [pscustomobject]@{ Id = "144q6GVWyIx7aJVjoe2FN2P35Z9eATPv9"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\hallway_straight_ccw_part_1.bag" },
    [pscustomobject]@{ Id = "1nkYMSyEH0Lk_p8eCH0WTBw8H_2U16E9i"; Group = "bags"; RelativePath = "Jun. 15, 2022\Original Bags\hallway_straight_ccw_part_2.bag" },

    [pscustomobject]@{ Id = "15-6AxGxLR7CbbiHlMwFk0GxG_x7XTgyN"; Group = "zips"; RelativePath = "Jun. 15, 2022\Aisle_CCW_Run_1.zip" },
    [pscustomobject]@{ Id = "1qOBEsoLn0P8NGUUaUXst95WHF_gqr4z7"; Group = "zips"; RelativePath = "Jun. 15, 2022\Aisle_CCW_Run_2.zip" },
    [pscustomobject]@{ Id = "1nNVQRZc4c1FNLjyKdueJ_bsBySCoVKRc"; Group = "zips"; RelativePath = "Jun. 15, 2022\Aisle_CW_Run_1.zip" },
    [pscustomobject]@{ Id = "1CVGFmK8wf1atpnj_3XQegpCgVESozJn6"; Group = "zips"; RelativePath = "Jun. 15, 2022\Aisle_CW_Run_2.zip" },
    [pscustomobject]@{ Id = "1acVszk2ZxZ-HZ1wlthNXHOHV5tSihJVp"; Group = "zips"; RelativePath = "Jun. 15, 2022\Hallway_Full_CCW.zip" },
    [pscustomobject]@{ Id = "1F6FR8DhX9VJ7l70Drs4EiSqtglb1-L_p"; Group = "zips"; RelativePath = "Jun. 15, 2022\Hallway_Full_CW.zip" },
    [pscustomobject]@{ Id = "1mV0j0ysm7Za1CIXSzMbsIzHu090RCbPs"; Group = "zips"; RelativePath = "Jun. 15, 2022\Hallway_Straight_CCW.zip" },

    [pscustomobject]@{ Id = "1rbgbtwLHKRymm2AiSq1Ap7rotdauS7iD"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\aisle_ccw_run_1.bag" },
    [pscustomobject]@{ Id = "1834fiFD2MoKRK15SIrrwadVg27XUCfbi"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\aisle_ccw_run_2.bag" },
    [pscustomobject]@{ Id = "1B_tw3K1WUk98IrAxbLiR-2QzhIg-f8oK"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\aisle_cw_run_1.bag" },
    [pscustomobject]@{ Id = "1CgvBhhEZFPMATLBNfULeHw8SmWxUP8Cr"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\aisle_cw_run_2.bag" },
    [pscustomobject]@{ Id = "1tGEbs0jlIseco2vVvYH5yS9xCf4XbRLs"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\hallway_full_cw_part_1.bag" },
    [pscustomobject]@{ Id = "1gFeF57iFNRaT_OenUIZfB1KXeEKQcVb4"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\hallway_full_cw_part_2.bag" },
    [pscustomobject]@{ Id = "1q00whMpJhBCyugA4YCmgW2nis7aAzWjQ"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\hallway_straight_ccw_part_1.bag" },
    [pscustomobject]@{ Id = "1t8tZgSNdkc7Jkq8EbCm5ED0efw4zbZ-e"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\hallway_straight_ccw_part_2.bag" },
    [pscustomobject]@{ Id = "17Puam3euR19qkw-T06EoNRz-QnOfur9q"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\hallway_straight_cw_part_1.bag" },
    [pscustomobject]@{ Id = "1yG8DNoe55RkpPUFwsnUvMZCQ216ridM8"; Group = "bags"; RelativePath = "Jun. 23, 2022\Original Bags\hallway_straight_cw_part_2.bag" },

    [pscustomobject]@{ Id = "1T-n-6Ou3SPM3zT863ArohAUa768ufr0c"; Group = "zips"; RelativePath = "Jun. 23, 2022\Aisle_CCW_Run_1.zip" },
    [pscustomobject]@{ Id = "1a5KcRGQO9QY-JUlZPDLcFu4LRS5sZrxj"; Group = "zips"; RelativePath = "Jun. 23, 2022\Aisle_CCW_Run_2.zip" },
    [pscustomobject]@{ Id = "1NymBUWtHWLL15bYaXBJiDJa74gnNHgmR"; Group = "zips"; RelativePath = "Jun. 23, 2022\Aisle_CW_Run_1.zip" },
    [pscustomobject]@{ Id = "16xeV4qeKWKk9zNv-BUykC-A8GRrJP8Ak"; Group = "zips"; RelativePath = "Jun. 23, 2022\Aisle_CW_Run_2.zip" },
    [pscustomobject]@{ Id = "1cMxZeduI_TQPUpfFpOVBDtES0H6Mgpt2"; Group = "zips"; RelativePath = "Jun. 23, 2022\Hallway_Full_CW.zip" },
    [pscustomobject]@{ Id = "1oke7tQJrshs9M9i7in-PzpCgaW7mh9Y-"; Group = "zips"; RelativePath = "Jun. 23, 2022\Hallway_Straight_CCW.zip" },
    [pscustomobject]@{ Id = "1x0xrfXZAlpjuvtfvtCPbbKzaFMi9jgMu"; Group = "zips"; RelativePath = "Jun. 23, 2022\Hallway_Straight_CW.zip" },

    [pscustomobject]@{ Id = "1CZlwpLNQq61i5b7AS1Ks21RY5XG5m8fZ"; Group = "bags"; RelativePath = "Oct. 12, 2022\Original Bags\aisle_ccw.bag" },
    [pscustomobject]@{ Id = "1rq7oBvXuAPP6znrUKQQczaYZUA-NkoBG"; Group = "bags"; RelativePath = "Oct. 12, 2022\Original Bags\aisle_cw.bag" },
    [pscustomobject]@{ Id = "1dErJnUXJj5WZ1EE2LuA-ZnRFZOHO4M4E"; Group = "bags"; RelativePath = "Oct. 12, 2022\Original Bags\hallway_full_cw_run1.bag" },
    [pscustomobject]@{ Id = "1XHiTGLy1EKbq7ZzMvgk9ke6NStd1wY1n"; Group = "bags"; RelativePath = "Oct. 12, 2022\Original Bags\hallway_full_cw_run2.bag" },
    [pscustomobject]@{ Id = "1lHPRCJr6dmPJKy4tI0UDR_lEPQiXttL-"; Group = "bags"; RelativePath = "Oct. 12, 2022\Original Bags\hallway_straight_ccw.bag" },
    [pscustomobject]@{ Id = "1Dfk2kKw3qxmfjr_fkHCx3ccF9er9GBWz"; Group = "bags"; RelativePath = "Oct. 12, 2022\Original Bags\hallway_straight_cw.bag" },

    [pscustomobject]@{ Id = "1hplx0_5tDKz4zF6iRgTfwuQNIund0URn"; Group = "zips"; RelativePath = "Oct. 12, 2022\Aisle_CCW.zip" },
    [pscustomobject]@{ Id = "1_ESM_9B_Xgqe1hDJmvqn83U6Dx-efarb"; Group = "zips"; RelativePath = "Oct. 12, 2022\Aisle_CW.zip" },
    [pscustomobject]@{ Id = "1cpQ2VvbJsgQWtX0HTz9nGLoAl-pQbx2I"; Group = "zips"; RelativePath = "Oct. 12, 2022\Hallway_Full_CW_Run_1.zip" },
    [pscustomobject]@{ Id = "1tcHtf7QqNzmgYyX60qiyaWkWNngbB6Nn"; Group = "zips"; RelativePath = "Oct. 12, 2022\Hallway_Full_CW_Run_2.zip" },
    [pscustomobject]@{ Id = "11MlBaWifh8Leh35vEaTpKb9EEC8KNe94"; Group = "zips"; RelativePath = "Oct. 12, 2022\Hallway_Straight_CCW.zip" },
    [pscustomobject]@{ Id = "1nIXeky1OmbQ2V1ROtBoBirlIPZ6h3ArJ"; Group = "zips"; RelativePath = "Oct. 12, 2022\Hallway_Straight_CW.zip" },
    [pscustomobject]@{ Id = "1NVnNEi-9QDoeyrnkxtlv8dHZl4Sc79zw"; Group = "zips"; RelativePath = "Oct. 12, 2022\calibrations.txt" },
    [pscustomobject]@{ Id = "1SsgnWfJeK9Hly5yfrq461MSXcdgyectN"; Group = "zips"; RelativePath = "Oct. 12, 2022\groundtruth_map.ply" },
    [pscustomobject]@{ Id = "1ovm4ycVrQfpuseI2Kc8TofS-LI0Nly_I"; Group = "zips"; RelativePath = "Oct. 12, 2022\AnnotatedSemanticSet_Finetuning.zip" }
)

switch ($Mode) {
    "bags" { $selected = $items | Where-Object { $_.Group -eq "bags" } }
    "all"  { $selected = $items }
    default { $selected = $items | Where-Object { $_.Group -eq "zips" } }
}

$success = New-Object System.Collections.Generic.List[string]
$failed = New-Object System.Collections.Generic.List[string]
$skipped = New-Object System.Collections.Generic.List[string]

foreach ($item in $selected) {
    if ($blockedIds -contains $item.Id) {
        $skipped.Add($item.RelativePath) | Out-Null
        Write-Host "SKIP quota-limited:" $item.RelativePath
        continue
    }

    $target = Join-Path $root $item.RelativePath
    $parent = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    $done = $false
    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        Write-Host ("[{0}/{1}] {2}" -f $attempt, $Retries, $item.RelativePath)
        python -m gdown --continue --id $item.Id -O $target
        if ($LASTEXITCODE -eq 0) {
            $success.Add($item.RelativePath) | Out-Null
            $done = $true
            break
        }
        Start-Sleep -Seconds 3
    }

    if (-not $done) {
        $failed.Add($item.RelativePath) | Out-Null
    }
}

Write-Host ""
Write-Host "Summary"
Write-Host ("Success: {0}" -f $success.Count)
Write-Host ("Failed:  {0}" -f $failed.Count)
Write-Host ("Skipped: {0}" -f $skipped.Count)

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed files:"
    $failed | ForEach-Object { Write-Host $_ }
}

if ($skipped.Count -gt 0) {
    Write-Host ""
    Write-Host "Skipped files:"
    $skipped | ForEach-Object { Write-Host $_ }
}

if ($failed.Count -gt 0) {
    exit 1
}
