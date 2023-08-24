import { useEffect, useState } from "react";
import { Stack, TextField } from "@fluentui/react";
import { SendRegular } from "@fluentui/react-icons";
import Send from "../../assets/Send.svg";
import styles from "./GenAISummary.module.css"
import { summaryApi,langSummaryApi } from "../../api";
const GenAISummary = () => {
    const [genAIContent, setGenAIContent] = useState<string>("");
    const [genAIContentSummary, setGenAIContentSummary] = useState<string>("No Summary to display.");

    const onGenAISummaryChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setGenAIContent(newValue || "");
    };

    const sendGenAIContent = async () => {
      //let data = "Once, there was a boy who became bored when he watched over the village sheep grazing on the hillside. To entertain himself, he sang out, “Wolf! Wolf! The wolf is chasing the sheep!”.When the villagers heard the cry, they came running up the hill to drive the wolf away. But, when they arrived, they saw no wolf. The boy was amused when seeing their angry faces. “Don’t scream wolf, boy,” warned the villagers, “when there is no wolf!” They angrily went back down the hill. Later, the shepherd boy cried out once again, “Wolf! Wolf! The wolf is chasing the sheep!” To his amusement, he looked on as the villagers came running up the hill to scare the wolf away. As they saw there was no wolf, they said strictly, “Save your frightened cry for when there really is a wolf! Don’t cry ‘wolf’ when there is no wolf!” But the boy grinned at their words while they walked grumbling down the hill once more.Later, the boy saw a real wolf sneaking around his flock. Alarmed, he jumped on his feet and cried out as loud as he could, “Wolf! Wolf!” But the villagers thought he was fooling them again, and so they didn’t come to help. At sunset, the villagers went looking for the boy who hadn’t returned with their sheep. When they went up the hill, they found him weeping.“There really was a wolf here! The flock is gone! I cried out, ‘Wolf!’ but you didn’t come,” he wailed.An old man went to comfort the boy. As he put his arm around him, he said, “Nobody believes a liar, even when he is telling the truth!”.So the moral of the story is Lying breaks trust — even if you’re telling the truth, no one believes a liar."
      //setLangContent(data);
      if(genAIContent && genAIContent != '')
      {
      let textdata:any = {
        text: genAIContent
      }
      setGenAIContentSummary("Generating Summary...")
      const response = await summaryApi(textdata);
      const processedText :any = await response.text()
      const processedTextJSON :any = JSON.parse(processedText)
       console.log("processedTextjson", JSON.parse(processedText));
       console.log("processedText", processedText.content);
       setGenAIContentSummary(processedTextJSON.content)
      }
    };

    return (
      <div role="main">
        <Stack className={styles.chatRoots}>
        <Stack className={styles.questionInputContainer}>
          <div className={styles.titlemain}>Generative AI Api</div>
          <div className={styles.textform}>
          <TextField
            className={styles.questionInputTextArea}
            placeholder="Enter content here..."
            multiline
            resizable={false}
            borderless
            value={genAIContent}
            onChange={onGenAISummaryChange}
          />
          <div
            className={styles.questionInputSendButtonContainer}
            role="button"
            tabIndex={0}
            aria-label="Ask question button"
            onClick={sendGenAIContent}
            onKeyDown={(e) =>
              e.key === "Enter" || e.key === " " ? sendGenAIContent() : null
            }
          >
          <img src={Send} className={styles.questionInputSendButton} />
          </div>
          <div className={styles.questionInputBottomBorder} />
          </div>
        
        </Stack>
        <div className={styles.title}><b>Gen AI Summary:</b> {genAIContentSummary != ''?genAIContentSummary:'No summary yet..'}</div>
        </Stack>
      </div>
    );
};

export default GenAISummary;
