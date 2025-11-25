#pragma once

#include <QGridLayout>
#include <QLabel>
#include <QLineEdit>
#include <QMap>
#include <QVector>
#include <QWidget>

struct GroupSpec {
    QString title;
    int count;
};

class SectionPanel : public QWidget {
    Q_OBJECT

public:
    explicit SectionPanel(const QString &sectionName,
                          const QVector<GroupSpec> &groups,
                          QWidget *parent = nullptr);

    QStringList answers() const;
    QStringList answerKeys() const;
    int questionCount() const;
    void clearAnswers();
    void clearKeys();
    void resetFeedback();
    QPair<int, int> evaluate();
    void setKeysVisible(bool visible);
    void applyParsedAnswers(const QMap<int, QString> &mapping);

private:
    QString sectionName_;
    QVector<GroupSpec> groups_;
    QVector<QLineEdit *> userEdits_;
    QVector<QLineEdit *> keyEdits_;
    QVector<QLabel *> statusLabels_;
    bool keysVisible_ = true;

    void buildGrid();
};

