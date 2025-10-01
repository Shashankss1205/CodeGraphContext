import React, { useState, useEffect } from "react";

const MoveToTop: React.FC = () => {
    const [showButton, setShowButton] = useState<boolean>(false);

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > window.innerHeight * 0.05) {
                setShowButton(true);
            } else {
                setShowButton(false);
            }
        };

        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    return (
        <>
            {showButton && (
                <button
                    onClick={scrollToTop}
                    style={{
                        position: "fixed",
                        bottom: "40px",
                        right: "40px",
                        width: "40px",
                        height: "40px",
                        borderRadius: "50%",
                        border: "none",
                        background: "linear-gradient(135deg, hsl(263 70% 65%), hsl(180 100% 70%))",
                        color: "#fff",
                        cursor: "pointer",
                        zIndex: 99,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        padding: 0,
                    }}
                >
                    <div
                        style={{
                            width: "14px",
                            height: "14px",
                            borderTop: "1.5px solid black",
                            borderLeft: "1.5px solid black",
                            transform: "rotate(45deg) translateY(3px) translateX(2px)",
                        }}
                    ></div>
                </button>
            )}
        </>
    );
};

export default MoveToTop;
