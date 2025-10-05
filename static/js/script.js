document.addEventListener("DOMContentLoaded", function() {
    // var lastScrollTop = 0;
    // var header = document.querySelector(".fixed-header");

    // window.addEventListener("scroll", function() {
    //     var currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        
    //     // 上にスクロールした場合、ヘッダーを表示
    //     if (currentScroll < lastScrollTop) {
    //         header.style.top = "0";
    //     } 
    //     // 下にスクロールした場合、ヘッダーを非表示
    //     else if (currentScroll > lastScrollTop) {
    //         header.style.top = "-100px"; // ヘッダーの高さに合わせて調整してください
    //     }
        
    //     // 0以下にならないようにする
    //     lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    // }, false);

    /**
     * グローバルスクロール位置管理
     * 
     * このコードは意図的にscript.jsに配置しています。
     * 理由：
     * 1. アプリケーション全体で使用される基本機能
     * 2. フレームワークに依存しない汎用的な実装
     * 3. ページ間のスクロール位置の一貫性を保つため
     * 
     * 使用例：
     * - ページネーション間の移動
     * - 詳細ページから一覧への戻り
     * - 検索結果ページでの位置保持
     */
    var scrollPosition = localStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        localStorage.removeItem('scrollPosition');
    }

    // document.querySelectorAll('.pagination a').forEach(link => {
    //     link.onclick = function() {
    //         localStorage.setItem('scrollPosition', window.pageYOffset.toString());
    //     };
    // });

    // const likeButtons = document.querySelectorAll('.like-button');
    // likeButtons.forEach(function(likeButton) {
    //     likeButton.addEventListener('click', function(e) {
    //         e.preventDefault();
    //         const novelId = this.dataset.novelId;
    //         const csrftoken = getCookie('csrftoken');
    //         fetch(`/novels/${novelId}/like/`, {
    //             method: 'POST',
    //             headers: {
    //                 'X-CSRFToken': csrftoken,
    //                 'Content-Type': 'application/json',
    //             },
    //             body: JSON.stringify({ 'novel_id': novelId }),
    //         })
    //         .then(response => response.json())
    //         .then(data => {
    //             const likeIcon = this.querySelector('.like-icon');
    //             likeIcon.src = data.is_liked ? this.dataset.likeImg : this.dataset.unlikeImg;
    //             const likeCount = this.nextElementSibling;
    //             likeCount.textContent = data.likes_count;
    //         })
    //         .catch(error => console.error('Error:', error));

    //         const likeIcon = this.querySelector('.like-icon');
    //         likeIcon.classList.add('rotate-effect');

    //         const sparkle = document.createElement('span');
    //         sparkle.classList.add('sparkle-effect');
    //         sparkle.textContent = '✨';
    //         this.appendChild(sparkle);

    //         sparkle.addEventListener('animationend', function() {
    //             sparkle.remove();
    //         });

    //         likeIcon.addEventListener('animationend', function() {
    //             likeIcon.classList.remove('rotate-effect');
    //         });
    //     });
    // });

    // const userNickname = document.getElementById('user-nickname');
    // const dropdownMenu = document.getElementById('dropdown-menu');
    // if (userNickname && dropdownMenu) {
    //     userNickname.addEventListener('click', function(event) {
    //         console.log("ニックネームがクリックされました。"); // この行を追加
    //         event.preventDefault();
    //         dropdownMenu.style.display = dropdownMenu.style.display === "none" || !dropdownMenu.style.display ? "block" : "none";
    //     });
    // }

    // 以下ヘッダーをスクロールで出したり引っ込めたりの部分
    // ヘッダーの高さを設定する関数
    // function setHeaderHeight() {
    //     var headerHeight = document.querySelector(".fixed-header").offsetHeight;
    //     document.querySelector(".main-content").style.paddingTop = headerHeight + "px";
    // }

    // // 初期ロード時にヘッダーの高さを設定
    // setHeaderHeight();

    // // ウィンドウのサイズが変更された時にヘッダーの高さを再設定
    // window.addEventListener('resize', setHeaderHeight);

    // // ヘッダーの高さに基づいてメインコンテンツのpadding-topを設定
    // var headerHeight = document.querySelector(".fixed-header").offsetHeight;
    // document.querySelector(".main-content").style.paddingTop = headerHeight + "px";

// コメントの既読・未読を切り替えるボタンにイベントリスナーを追加
// document.querySelectorAll('.toggle-read-status').forEach(function(checkbox) {
//     checkbox.addEventListener('change', function() {
//         console.log('Dataset:', this.dataset); // datasetの内容を確認
//         const commentId = this.dataset.commentId;
//         const novelId = this.dataset.novelId; // 小説のIDを取得
//         console.log('Novel ID:', novelId); // novelIdの値を確認
//         const isRead = this.checked;

//         // toggleReadStatus 関数を呼び出して、コメントの既読状態を切り替える
//         toggleReadStatus(commentId, isRead, novelId);
//     });
// });

// ページ読み込み時と定期的に未読コメント数を更新
// updateUnreadCommentsCount();
// setInterval(updateUnreadCommentsCount, 60000); // 1分ごとに更新


    // // タイトルの文字数を更新する関数
    // function updateTitleWordCount() {
    //     const titleField = document.querySelector('.title');
    //     const titleWordCountDisplay = document.getElementById('titleWordCount');
    //     if (titleField && titleWordCountDisplay) {
    //         const titleWordCount = titleField.value.length;
    //         titleWordCountDisplay.textContent = `${titleWordCount} / 30文字`;
    //     }
    // }

    // // タイトル入力フィールドにイベントリスナーを追加
    // const titleField = document.querySelector('.title');
    // if (titleField) {
    //     titleField.addEventListener('input', updateTitleWordCount);
    //     updateTitleWordCount(); // ページ読み込み時にタイトルの文字数を更新
    // }

    // // 小説の内容入力フィールドを取得し、以前の宣言を削除またはコメントアウト
    // const contentInput = document.querySelector('.content'); // この行は残す




    // // 文字数を表示する要素を取得
    // const wordCountDisplay = document.getElementById('wordCount');

    // // フッターの文字数カウンターを表示する要素を取得
    // const footerWordCountDisplay = document.getElementById('footerWordCount');

    // // 文字数を更新する関数
    // function updateFooterWordCount() {
    //     if (contentInput && footerWordCountDisplay) {
    //         const count = contentInput.value.length;
    //         const formattedCount = count.toLocaleString();
    //         const formattedMax = (10000).toLocaleString(); // 最大文字数もフォーマット
    //         footerWordCountDisplay.textContent = `${formattedCount} / ${formattedMax}文字`;
    //     }
    // }

    // // コンテンツ入力フィールドに 'click' と 'input' イベントリスナーを追加
    // if (contentInput) {
    //     // コンテンツ入力フィールドに 'click' と 'input' イベントリスナーを追加
    //     contentInput.addEventListener('click', updateFooterWordCount);
    //     contentInput.addEventListener('input', updateFooterWordCount);
    // }
    
    // テキストエリアの高さを計算して、高さ８５％のテキストエリアにする。
    const contentTextarea = document.querySelector('.content');
    if (contentTextarea) {
        function setInitialTextareaHeight() {
            // 画面の縦幅から、テキストエリア以外の要素の高さを引いた値をテキストエリアの高さとする
            // ここでは例として、画面の100%の高さをテキストエリアに設定しています
            const screenHeight = window.innerHeight;
            const otherElementsHeight = 100; // ヘッダー、フッター、マージンなどの高さの合計を推定
            const textareaHeight = screenHeight - otherElementsHeight; // 画面の100%からその他要素の高さを引く
            contentTextarea.style.height = `${textareaHeight}px`;
        }

        // ページ読み込み時に一度だけテキストエリアの高さを設定
        setInitialTextareaHeight();
    }

    // ログアウトアイコンのクリックイベントを処理
    // const logoutIcon = document.getElementById('logout-icon');
    // if (logoutIcon) {
    //     logoutIcon.addEventListener('click', function(event) {
    //         event.preventDefault();
    //         const logoutConfirmed = confirm("ログアウトするっすか？");
    //         if (logoutConfirmed) {
    //             logout();
    //         }
    //     });
    // }

    // コメントテキストエリアの文字数カウントと警告メッセージの表示
    // const commentTextarea = document.querySelector('.comment-textarea');
    // if (commentTextarea) { // コメントテキストエリアが存在する場合のみ実行
    //     const feedback = document.createElement('div');
    //     feedback.id = 'comment-feedback';
    //     commentTextarea.parentNode.insertBefore(feedback, commentTextarea.nextSibling);

    //     commentTextarea.addEventListener('input', function () {
    //         const remaining = 1000 - this.value.length;
    //         if (remaining < 0) {
    //             feedback.innerHTML = '<span style="color: red;">コメントは1000文字までです！</span>';
    //         } else {
    //             feedback.innerHTML = '残り ' + remaining + ' 文字';
    //         }
    //     });
    // }



/**
 * メッセージの表示/非表示を制御する共通機能
 * 
 * この機能は以下の場所で使用：
 * 1. 小説編集画面（post_or_edit_novel.html）
 *    - 編集プレビュー後の説明メッセージ
 * 2. その他のチュートリアル的なメッセージ
 * 
 * 使用方法：
 * <p class="toggle-message" id="message-warning" style="display:none;">
 *     メッセージ内容
 *     <button class="toggle-message-button">非表示</button>
 * </p>
 * 
 * @param {string} messageId - メッセージ要素のID
 * @param {string} storageKey - localStorage用のキー名
 */
function toggleMessageVisibility(messageId, storageKey) {
    const messageShown = localStorage.getItem(storageKey);
    const messageElement = document.getElementById(messageId);

    // messageElement が null でないことを確認
    if (messageElement) {
        // メッセージがまだ表示されていない場合は、メッセージを表示する
        if (messageShown !== 'true') {
            messageElement.style.display = 'block';
        }

        // メッセージの非表示ボタンクリックイベントを設定
        const button = messageElement.querySelector('.toggle-message-button');
        if (button) {
            button.addEventListener('click', function() {
                // 確認ダイアログを表示
                const confirmHide = confirm("このメッセージを非表示にしますか？");
                if (confirmHide) {
                    // ユーザーが「はい」を選択した場合、メッセージを非表示にする
                    messageElement.style.display = 'none';
                    localStorage.setItem(storageKey, 'true');
                }
            });
        }
    } else {
        // messageElement が null の場合、警告をログに出力
        console.warn(`Element with ID ${messageId} not found.`);
    }
}


});





/**
 * CSRFトークンを取得するユーティリティ関数
 * 
 * このコードは意図的にscript.jsに配置しています。
 * 理由：
 * 1. アプリケーション全体でPOSTリクエスト時に必要
 * 2. セキュリティ関連の処理は統一的に管理すべき
 * 3. 各ページでの実装の重複を避ける
 * 
 * 主な使用場面：
 * - 小説関連：投稿、編集、削除、いいね
 * - コメント関連：投稿、既読/未読切り替え
 * - ユーザー関連：プロフィール更新、設定変更
 * - その他：フォーム送信全般、APIリクエスト
 * 
 * @param {string} name - クッキーの名前（通常は'csrftoken'）
 * @returns {string|null} 取得したCSRFトークン、または取得できない場合はnull
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

    // document.querySelectorAll('.comment').forEach(function(comment) {
    //     const content = comment.querySelector('.comment-content');
        
    //     // 一時的に制限を解除して実際の高さを取得
    //     content.style.maxHeight = 'none';
    //     const contentHeight = content.offsetHeight;
        
    //     // 80pxより高い場合のみ縮める処理を適用
    //     if (contentHeight > 80) {
    //         content.style.maxHeight = '80px';
    //         content.style.overflow = 'hidden';
            
    //         // ボタンを配置するdivを作成
    //         const buttonContainer = document.createElement('div');
    //         buttonContainer.style.marginTop = '5px';
            
    //         // もっと見る/縮めるボタンを作成
    //         const button = document.createElement('button');
    //         button.textContent = 'もっと見る';
    //         button.classList.add('toggle-button');
            
    //         // コメント枠の後ろにボタンコンテナを配置
    //         comment.after(buttonContainer);
    //         buttonContainer.appendChild(button);
            
    //         button.addEventListener('click', function() {
    //             if (content.style.maxHeight === '80px') {
    //                 content.style.maxHeight = 'none';
    //                 button.textContent = '▲ 縮める';
    //             } else {
    //                 content.style.maxHeight = '80px';
    //                 button.textContent = 'もっと見る';
    //             }
    //         });
    //     }
    // }
// );






// // コメントフォームの送信をハンドルする関数
// function handleCommentSubmit(event) {
//     event.preventDefault();
//     const form = event.target;
//     const formData = new FormData(form);

//     fetch(form.action, {
//         method: 'POST',
//         body: formData,
//         headers: {
//             'X-Requested-With': 'XMLHttpRequest'
//         }
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.success) {
//             // コメントリストを更新
//             loadComments();
//             // フォームをリセット
//             form.reset();
//         }
//     })
//     .catch(error => console.error('Error:', error));
// }

//     // コメントフォームにイベントリスナーを追加
//     document.addEventListener('DOMContentLoaded', function() {
//         const commentForm = document.getElementById('comment-form');
//         if (commentForm) {
//             commentForm.addEventListener('submit', handleCommentSubmit);
//         }
//     });