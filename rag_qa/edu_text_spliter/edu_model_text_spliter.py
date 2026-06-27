try:
    from langchain_text_splitters import CharacterTextSplitter
except ImportError:
    from langchain.text_splitter import CharacterTextSplitter
import re
from typing import List


class AliTextSplitter(CharacterTextSplitter):
    def __init__(self, pdf: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pdf = pdf

    def split_text(self, text: str) -> List[str]:
        # 延迟导入 modelscope，避免未安装时阻塞整个项目
        try:
            from modelscope.pipelines import pipeline
        except ImportError:
            # modelscope 未安装时，回退到简单按句号分句
            return [s.strip() for s in re.split(r'[。！？\n]', text) if s.strip()]

        if self.pdf:
            text = re.sub(r"\n{3,}", r"\n", text)
            text = re.sub(r'\s', " ", text)
            text = re.sub(r"\n\n", "", text)

        p = pipeline(
            task="document-segmentation",
            model='damo/nlp_bert_document-segmentation_chinese-base',
            device="cpu",
        )
        result = p(documents=text)
        sent_list = [i for i in result["text"].split("\n\t") if i]
        return sent_list


if __name__ == '__main__':
    model_split = AliTextSplitter()
    result = model_split.split_text(text='移动端语音唤醒模型...')
    print(result)
