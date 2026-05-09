.PHONY: build-image run demo semantic-example dynamic-slam-frontend dynamic-slam-backend-pack dynamic-slam-backend-env-check dynamic-slam-backend-smoke evidence-pack

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

evidence-pack:
	python tools/build_paper_evidence_pack.py
