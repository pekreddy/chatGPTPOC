import { Outlet, Link } from "react-router-dom";
import styles from "./Layout.module.css";
import Azure from "../../assets/NewLogo.png";
import { CopyRegular, ShareRegular } from "@fluentui/react-icons";
import { Dialog, Stack, TextField } from "@fluentui/react";
import { useEffect, useState, useRef } from "react";
import { ContextualMenu, ContextualMenuItemType, IContextualMenuItem } from '@fluentui/react/lib/ContextualMenu';
import  Chat from "../chat/Chat";
import Summary from "../summary/Summary";
import GenAISummary from "../genaisummary/GenAISummary";

const Layout = () => {
    const [isSharePanelOpen, setIsSharePanelOpen] = useState<boolean>(false);
    const [copyClicked, setCopyClicked] = useState<boolean>(false);
    const [copyText, setCopyText] = useState<string>("Copy URL");
    const [showContextualMenu, setShowContextualMenu] = useState(false);
    const linkRef = useRef(null);
    const [selectedTab, setSelectedTab] = useState("Chat");
    const menuItems: IContextualMenuItem[] = [
        {
          key: 'ChatBot',
          text: 'ChatBot',
          onClick: () => setSelectedTab("Chat")
        },
        {
            key: 'Summary',
            text: 'Summary',
            onClick: () => setSelectedTab("Summary")
        },
        {
            key: 'GenAISummary',
            text: 'GenAISummary',
            onClick: () => setSelectedTab("GenAISummary")
        }
      ];

    const onShowContextualMenu = () => {
        setShowContextualMenu(!showContextualMenu)
    }

    const handleShareClick = () => {
        setIsSharePanelOpen(true);
    };

    const handleSharePanelDismiss = () => {
        setIsSharePanelOpen(false);
        setCopyClicked(false);
        setCopyText("Copy URL");
    };

    const handleCopyClick = () => {
        navigator.clipboard.writeText(window.location.href);
        setCopyClicked(true);
    };

    useEffect(() => {
        if (copyClicked) {
            setCopyText("Copied URL");
        }
    }, [copyClicked]);

    return (
      <div className={styles.layout}>
        <header className={styles.header} role={"banner"}>
          <div className={styles.headerContainer}>
            <Stack horizontal verticalAlign="center">
              <img
                src={Azure}
                className={styles.headerIcon}
                aria-hidden="true"
              />
              <Link to="/" className={styles.headerTitleContainer}>
                <h1 className={styles.headerTitle}>KX GenAI Cognitive</h1>
              </Link>
              <Link to="/elastic" className={styles.headerTitleContainer}>
                <h1 className={styles.headerTitle}>KX GenAI Elastic</h1>
              </Link>
              <div className={styles.shareButtonContainer}>
                <p>
                  <b>
                    <a ref={linkRef} onClick={onShowContextualMenu} href="#">
                      DashBoard
                    </a>
                  </b>
                </p>
              </div>
              <ContextualMenu
                items={menuItems}
                hidden={!showContextualMenu}
                target={linkRef}
                onItemClick={()=>{setShowContextualMenu(false)}}
                onDismiss={()=>{setShowContextualMenu(false)}}
              />
            </Stack>
          </div>
        </header>
        {/* <Outlet /> */}
        
        {selectedTab == "Chat" && <Chat/>}
        {selectedTab == "GenAISummary" && <GenAISummary/>}
        {selectedTab == "Summary" && <Summary/>}
      </div>
    );
};

export default Layout;
