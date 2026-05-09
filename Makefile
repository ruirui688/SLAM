.PHONY: build-image run demo semantic-example dynamic-slam-frontend dynamic-slam-backend-pack dynamic-slam-backend-env-check dynamic-slam-backend-smoke dynamic-slam-backend-64 dynamic-slam-backend-semantic-masks dynamic-slam-backend-temporal-mask-stress dynamic-slam-backend-flow-mask-stress dynamic-slam-backend-figure dynamic-mask-coverage-figure dynamic-temporal-mask-stress-figure dynamic-flow-mask-stress-figure evidence-pack

# Get version of CUDA and enable it for compilation if CUDA > 11.0
# This solves https://github.com/IDEA-Research/Grounded-Segment-Anything/issues/53
# and https://github.com/IDEA-Research/Grounded-Segment-Anything/issues/84
# when running in Docker
# Check if nvcc is installed
NVCC := $(shell which nvcc)
ifeq ($(NVCC),)
	# NVCC not found
	USE_CUDA := 0
	NVCC_VERSION := "not installed"
else
	NVCC_VERSION := $(shell nvcc --version | grep -oP 'release \K[0-9.]+')
	USE_CUDA := $(shell echo "$(NVCC_VERSION) > 11" | bc -l)
endif

# Add the list of supported ARCHs
ifeq ($(USE_CUDA), 1)
	TORCH_CUDA_ARCH_LIST := "7.0;7.5;8.0;8.6+PTX"
	BUILD_MESSAGE := "I will try to build the image with CUDA support"
else
	TORCH_CUDA_ARCH_LIST :=
	BUILD_MESSAGE := "CUDA $(NVCC_VERSION) is not supported"
endif


build-image:
	@echo $(BUILD_MESSAGE)
	docker build --build-arg USE_CUDA=$(USE_CUDA) \
	--build-arg TORCH_ARCH=$(TORCH_CUDA_ARCH_LIST) \
	-t grounded_sam2:1.0 .
run:
	docker run --gpus all -it --rm --net=host --privileged \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	-v "${PWD}":/home/appuser/Grounded-SAM-2 \
	-e DISPLAY=$DISPLAY \
	--name=gsa \
	--ipc=host -it grounded_sam2:1.0

demo:
	python tools/run_minimal_demo.py

semantic-example:
	python tools/build_semantic_example_panel.py

dynamic-slam-frontend:
	python tools/build_dynamic_slam_frontend_demo.py

dynamic-slam-backend-pack:
	python tools/build_dynamic_slam_backend_input_pack.py

dynamic-slam-backend-env-check:
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/check_dynamic_slam_backend_env.py

dynamic-slam-backend-smoke:
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/run_dynamic_slam_backend_smoke.py

dynamic-slam-backend-64:
	python tools/build_dynamic_slam_backend_input_pack.py --frame-count 64 --output-dir outputs/dynamic_slam_backend_input_pack_64
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_64 --output-dir outputs/dynamic_slam_backend_smoke_p134_64_global_ba --frame-limit 64 --buffer 256 --global-ba

dynamic-slam-backend-semantic-masks:
	python tools/build_dynamic_slam_backend_input_pack.py --frame-count 64 --output-dir outputs/dynamic_slam_backend_input_pack_64_semantic_masks --dynamic-mask-summary-dir outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1/frontend_output
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_64_semantic_masks --output-dir outputs/dynamic_slam_backend_smoke_p135_64_semantic_masks_global_ba --frame-limit 64 --buffer 256 --global-ba
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_64_semantic_masks --output-dir outputs/dynamic_slam_backend_smoke_p135_64_semantic_masks_global_ba --artifact "P135 semantic-mask-coverage DROID-SLAM global BA metrics" --scope "64-frame TorWIC Aisle_CW_Run_1, DROID-SLAM global BA, masked input built from existing forklift semantic frontend masks." --masked-label "semantic masked RGB" --output-prefix p135_semantic_mask_metrics --interpretation "Existing semantic masks are connected to the backend, but their temporal coverage is still sparse. The next step is dynamic-mask generation or tracking across more of the trajectory."

dynamic-slam-backend-temporal-mask-stress:
	python tools/build_dynamic_slam_backend_input_pack.py --frame-count 64 --output-dir outputs/dynamic_slam_backend_input_pack_64_temporal_mask_stress --dynamic-mask-summary-dir outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1/frontend_output --temporal-propagation-radius 8 --dynamic-mask-dilation-px 4
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_64_temporal_mask_stress --output-dir outputs/dynamic_slam_backend_smoke_p136_64_temporal_mask_stress_global_ba --frame-limit 64 --buffer 256 --global-ba
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_64_temporal_mask_stress --output-dir outputs/dynamic_slam_backend_smoke_p136_64_temporal_mask_stress_global_ba --artifact "P136 temporal-mask propagation stress-test DROID-SLAM global BA metrics" --scope "64-frame TorWIC Aisle_CW_Run_1, DROID-SLAM global BA, masked input built by nearest-frame temporal propagation of existing semantic forklift masks within +/-8 frames plus 4 px dilation." --masked-label "temporal propagated masked RGB" --output-prefix p136_temporal_mask_stress_metrics --interpretation "This is a diagnostic stress test, not a true detector output. It tests whether increasing temporal mask coverage makes the backend sensitive to dynamic masking."

dynamic-slam-backend-flow-mask-stress:
	python tools/build_dynamic_slam_backend_input_pack.py --frame-count 64 --output-dir outputs/dynamic_slam_backend_input_pack_64_flow_mask_stress --dynamic-mask-summary-dir outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1/frontend_output --temporal-propagation-radius 8 --dynamic-mask-dilation-px 4 --temporal-propagation-mode flow
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_64_flow_mask_stress --output-dir outputs/dynamic_slam_backend_smoke_p137_64_flow_mask_stress_global_ba --frame-limit 64 --buffer 256 --global-ba
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_64_flow_mask_stress --output-dir outputs/dynamic_slam_backend_smoke_p137_64_flow_mask_stress_global_ba --artifact "P137 optical-flow mask propagation stress-test DROID-SLAM global BA metrics" --scope "64-frame TorWIC Aisle_CW_Run_1, DROID-SLAM global BA, masked input built by dense optical-flow propagation of existing semantic forklift masks within +/-8 frames plus 4 px dilation." --masked-label "flow propagated masked RGB" --output-prefix p137_flow_mask_stress_metrics --interpretation "This is a diagnostic stress test, not a true detector output. It tests whether optical-flow mask propagation improves over nearest-frame copying for backend sensitivity."

dynamic-slam-backend-figure:
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/plot_dynamic_slam_backend_results.py

dynamic-mask-coverage-figure:
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/plot_dynamic_mask_coverage_diagnostic.py

dynamic-temporal-mask-stress-figure:
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/plot_dynamic_mask_coverage_diagnostic.py --manifest outputs/dynamic_slam_backend_input_pack_64_temporal_mask_stress/backend_input_manifest.json --metrics outputs/dynamic_slam_backend_smoke_p136_64_temporal_mask_stress_global_ba/p136_temporal_mask_stress_metrics.json --output paper/figures/torwic_dynamic_mask_temporal_stress_p136.png --title "P136 stress test: temporal mask propagation increases coverage but not trajectory gain" --caption "Nearest-frame mask propagation covers 16/64 frames with 0.267% mean coverage; backend metrics remain effectively tied." --masked-label "temporal propagated masked RGB"

dynamic-flow-mask-stress-figure:
	LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$$LD_LIBRARY_PATH conda run -n tram python tools/plot_dynamic_mask_coverage_diagnostic.py --manifest outputs/dynamic_slam_backend_input_pack_64_flow_mask_stress/backend_input_manifest.json --metrics outputs/dynamic_slam_backend_smoke_p137_64_flow_mask_stress_global_ba/p137_flow_mask_stress_metrics.json --output paper/figures/torwic_dynamic_mask_flow_stress_p137.png --title "P137 stress test: optical-flow mask propagation remains neutral" --caption "Dense-flow propagation covers 16/64 frames; APE/RPE remain effectively tied, so detector-quality temporal masks are still needed." --masked-label "flow propagated masked RGB"

evidence-pack:
	python tools/build_paper_evidence_pack.py
