import os
import transformers
from langchain_huggingface import HuggingFacePipeline

class LLM_connector:
    
    def __init__(self, model_path: str=None, cuda: bool=False, device_map:dict=None, temperature:float =.1,
                 max_new_tokens:float=100, repetition_penalty:float=1.1, use_cache:bool=True, num_returns:int=1,
                 top_k:int=10, do_sample:bool=True, verbose:bool=False):
        self.verbose = verbose
        if model_path is None:
            raise AttributeError('Path to model is necessary to work.')
        if not os.path.isdir(model_path):
            raise AttributeError(f'Given path {model_path} is not a directory.')
        if cuda and not torch.cuda.is_available():
            raise ConnectionError('Cuda is not available.')
        if device_map is not None:
            cuda = True
        
        self.device = 'auto'
        if cuda and device_map is not None:
            self.device = device_map
        elif cuda:
            self.device = 0
            
        if self.verbose:
            print(self.device if self.device != 0 else 'GPU')
        
        self.model = None
        self.configModel(model_path,temperature,max_new_tokens,repetition_penalty,
                                      use_cache,num_returns,top_k,do_sample)
        if self.verbose:
            print('Model is ready!')
        
    def configModel(self,model_id,temperature,max_new_tokens,repetition_penalty,use_cache,num_returns,top_k,do_sample):
        model_config = transformers.AutoConfig.from_pretrained(model_id)
        model = transformers.AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            config=model_config,
            # quantization_config=quant_config,
            device_map = self.device,
        )
        model.eval()
        
        model.config.pad_token_id = model.config.eos_token_id
        tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, use_fast = True)
        tokenizer.pad_token = tokenizer.eos_token

        streamer = transformers.TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

        generate_text = transformers.pipeline(
            model=model, 
            tokenizer=tokenizer,
            return_full_text=True, 
            task='text-generation',
            temperature = temperature,#creativity of the model
            max_new_tokens=max_new_tokens,#float('inf'),
            use_cache=use_cache,
            streamer = streamer,
            repetition_penalty=repetition_penalty,
            eos_token_id=tokenizer.eos_token_id,
            num_return_sequences = num_returns,#for one version of the model answer
            top_k = top_k,#for better quality of generation (10 most likely tokens)
            do_sample = do_sample,
            )

        self.model = HuggingFacePipeline(pipeline = generate_text)