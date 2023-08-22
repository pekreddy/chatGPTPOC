import { useState } from "react";
import { Stack, TextField } from "@fluentui/react";
import { SendRegular } from "@fluentui/react-icons";
import Send from "../../assets/Send.svg";
import styles from "./Summary.module.css";
import { summaryApi,langSummaryApi } from "../../api";
const Summary = () => {
    const [content, setContent] = useState<string>("");
    const [langContent, setLangContent] = useState<string>("");
    const onSummaryChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setContent(newValue || "");
    };

    const onLangSummaryChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setLangContent(newValue || "");
    };

    const sendContent = async () => {
      let data = "Once, there was a boy who became bored when he watched over the village sheep grazing on the hillside. To entertain himself, he sang out, “Wolf! Wolf! The wolf is chasing the sheep!”.When the villagers heard the cry, they came running up the hill to drive the wolf away. But, when they arrived, they saw no wolf. The boy was amused when seeing their angry faces. “Don’t scream wolf, boy,” warned the villagers, “when there is no wolf!” They angrily went back down the hill. Later, the shepherd boy cried out once again, “Wolf! Wolf! The wolf is chasing the sheep!” To his amusement, he looked on as the villagers came running up the hill to scare the wolf away. As they saw there was no wolf, they said strictly, “Save your frightened cry for when there really is a wolf! Don’t cry ‘wolf’ when there is no wolf!” But the boy grinned at their words while they walked grumbling down the hill once more.Later, the boy saw a real wolf sneaking around his flock. Alarmed, he jumped on his feet and cried out as loud as he could, “Wolf! Wolf!” But the villagers thought he was fooling them again, and so they didn’t come to help. At sunset, the villagers went looking for the boy who hadn’t returned with their sheep. When they went up the hill, they found him weeping.“There really was a wolf here! The flock is gone! I cried out, ‘Wolf!’ but you didn’t come,” he wailed.An old man went to comfort the boy. As he put his arm around him, he said, “Nobody believes a liar, even when he is telling the truth!”.So the moral of the story is Lying breaks trust — even if you’re telling the truth, no one believes a liar."
      setContent(data);
      const response = await summaryApi(data);

       console.log("response", response);
    };

    const sendLangContent = async () => {
      let data = "Once, there was a boy who became bored when he watched over the village sheep grazing on the hillside. To entertain himself, he sang out, “Wolf! Wolf! The wolf is chasing the sheep!”.When the villagers heard the cry, they came running up the hill to drive the wolf away. But, when they arrived, they saw no wolf. The boy was amused when seeing their angry faces. “Don’t scream wolf, boy,” warned the villagers, “when there is no wolf!” They angrily went back down the hill. Later, the shepherd boy cried out once again, “Wolf! Wolf! The wolf is chasing the sheep!” To his amusement, he looked on as the villagers came running up the hill to scare the wolf away. As they saw there was no wolf, they said strictly, “Save your frightened cry for when there really is a wolf! Don’t cry ‘wolf’ when there is no wolf!” But the boy grinned at their words while they walked grumbling down the hill once more.Later, the boy saw a real wolf sneaking around his flock. Alarmed, he jumped on his feet and cried out as loud as he could, “Wolf! Wolf!” But the villagers thought he was fooling them again, and so they didn’t come to help. At sunset, the villagers went looking for the boy who hadn’t returned with their sheep. When they went up the hill, they found him weeping.“There really was a wolf here! The flock is gone! I cried out, ‘Wolf!’ but you didn’t come,” he wailed.An old man went to comfort the boy. As he put his arm around him, he said, “Nobody believes a liar, even when he is telling the truth!”.So the moral of the story is Lying breaks trust — even if you’re telling the truth, no one believes a liar."
      setLangContent(data);
      const response = await langSummaryApi(data);

       console.log("response", response);
    };

    return (
      <div className={styles.container} role="main">
        <Stack horizontal className={styles.chatRoot}>
        <Stack horizontal className={styles.questionInputContainer}>
          <div>Gen AI Completions Api</div>
          <TextField
            className={styles.questionInputTextArea}
            placeholder="Enter content here..."
            multiline
            resizable={false}
            borderless
            value={content}
            onChange={onSummaryChange}
          />
          <div
            className={styles.questionInputSendButtonContainer}
            role="button"
            tabIndex={0}
            aria-label="Ask question button"
            onClick={sendContent}
            onKeyDown={(e) =>
              e.key === "Enter" || e.key === " " ? sendContent() : null
            }
          >
            <img src={Send} className={styles.questionInputSendButton} />
          </div>
          <div className={styles.questionInputBottomBorder} />
        </Stack>

        <Stack horizontal className={styles.questionInputContainer}>
          <div>Language Studio AI Api</div>
          <TextField
            className={styles.questionInputTextArea}
            placeholder="Enter content here..."
            multiline
            resizable={false}
            borderless
            value={langContent}
            onChange={onLangSummaryChange}
          />
          <div
            className={styles.questionInputSendButtonContainer}
            role="button"
            tabIndex={0}
            aria-label="Ask question button"
            onClick={sendLangContent}
            onKeyDown={(e) =>
              e.key === "Enter" || e.key === " " ? sendLangContent() : null
            }
          >
          <img src={Send} className={styles.questionInputSendButton} />
          </div>
          <div className={styles.questionInputBottomBorder} />
        </Stack>
        </Stack>
      </div>
    );
};

export default Summary;
